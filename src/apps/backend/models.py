import datetime
import logging
import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import JSONField
from languages.fields import LanguageField


class Origin(models.Model):
    """Represents a Stud.IP instance from which requests originate."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1024, default="default")
    type = models.CharField(max_length=1024, default="default")
    api_endpoint = models.CharField(max_length=1024)
    api_key = models.CharField(max_length=1024, default="")

    def __str__(self):
        """String representation of an Origin object."""
        return "Origin: {} {}".format(self.name, self.api_endpoint)


class Degree(models.Model):
    """Represents various degrees, such as Bachelor, Master, ..."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=1024, null=True)
    origin = models.ForeignKey(Origin, on_delete=models.CASCADE)
    degree_origin_id = models.CharField(max_length=256)

    def __str__(self):
        """String representation of a Degree object."""
        return "Degree {} {}".format(self.name, self.origin.name)

    def serialize(self):
        response_data = {
            "data": [
                {
                    "type": "Degree",
                    "id": self.id,
                    "attributes": {
                        "name": self.name,
                        "description": self.description,
                        "origin": self.origin.name,
                        "origin_id": self.degree_origin_id,
                    },
                }
            ]
        }

        return response_data


class Subject(models.Model):
    """Represents a course of study (subject), like 'Informatik', 'Cognitive Science'.
    The name field uses the local name at student's origin institution.
    Subjects are linked via references to official ids from Destatis
    (https://www.destatis.de/DE/Methoden/Klassifikationen/BildungKultur/StudentenPruefungsstatistik.html)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)
    description = models.CharField(max_length=1024, null=True)
    keywords = models.CharField(max_length=1024, null=True)
    origin = models.ForeignKey(Origin, on_delete=models.CASCADE)
    subject_origin_id = models.CharField(max_length=256)
    destatis_subject_id = models.IntegerField(default=0)

    def __str__(self):
        """String representation of a Subject object."""
        return "Subject {} {}".format(self.name, self.origin.name)


class SiddataUser(models.Model):
    """A user of the Siddata Study Assistant (not a user for the django app frontend)
    attributes:
    user_origin_id:  User ID in the origin system (e.g. Stud.IP Uni OS)
    gender: Gender

    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    origin = models.ForeignKey(Origin, on_delete=models.CASCADE)
    user_origin_id = models.CharField(max_length=256)
    gender_brain = models.CharField(max_length=256, null=True)
    gender_social = models.CharField(max_length=256, null=True)
    data_donation = models.BooleanField(default=False)

    def __str__(self):
        """String representation of a SiddataUser object."""
        return "SiddataUser {} {}".format(self.id, self.origin.name)

    def serialize(self, include=None):  # noqa: C901
        """
        Converts SiddataUser instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        include = include or []

        recommenders = []
        included = []
        userrecommenders = SiddataUserRecommender.objects.filter(user=self).order_by("recommender__order")
        for userrecommender in userrecommenders:
            recommenders.append({"id": userrecommender.id, "type": "Recommender"})
            if "recommenders" in include:
                r_ser = userrecommender.serialize()
                for entry in r_ser["data"] + r_ser["included"]:
                    if entry not in included:
                        included.append(entry)

        response_data = {
            "data": [
                {
                    "type": "SiddataUser",
                    "id": self.id,
                    "attributes": {
                        "origin": self.origin.name,
                        "user_origin_id": self.user_origin_id,
                        "data_donation": self.data_donation,
                        "gender_brain": self.gender_brain,
                        "gender_social": self.gender_social,
                    },
                    "relationships": {"recommenders": {"data": recommenders}},
                }
            ],
        }

        courses_brain = "courses_brain" in include
        courses_social = "courses_social" in include
        if courses_brain or courses_social:
            cms = CourseMembership.objects.filter(user=self)
            if courses_brain:
                response_data["data"][0]["relationships"]["courses_brain"] = {"data": []}
            if courses_social:
                response_data["data"][0]["relationships"]["courses_social"] = {"data": []}

            for cm in cms:
                relationship = {"type": "StudipCourse", "id": cm.course.course_origin_id}
                if cm.share_brain and courses_brain:
                    response_data["data"][0]["relationships"]["courses_brain"]["data"].append(relationship)
                if cm.share_social and courses_social:
                    response_data["data"][0]["relationships"]["courses_social"]["data"].append(relationship)

        institutes_brain = "institutes_brain" in include
        institutes_social = "institutes_social" in include
        if institutes_brain or institutes_social:
            ims = InstituteMembership.objects.filter(user=self)
            if institutes_brain:
                response_data["data"][0]["relationships"]["institutes_brain"] = {"data": []}
            if institutes_social:
                response_data["data"][0]["relationships"]["institutes_social"] = {"data": []}

            for im in ims:
                relationship = {"type": "StudipInstitute", "id": im.institute.institute_origin_id}
                if im.share_brain and institutes_brain:
                    response_data["data"][0]["relationships"]["institutes_brain"]["data"].append(relationship)
                if im.share_social and institutes_social:
                    response_data["data"][0]["relationships"]["institutes_social"]["data"].append(relationship)

        if len(include) > 0:
            response_data["included"] = included

        return response_data

    def get_property(self, key):
        """Get a users's property identified by key.

        This encapsulates the user property handling with UserProperty objects.
        :return:The key's value is a string or None if key is not set."""
        UPs = UserProperty.objects.filter(user=self, key=key)
        if len(UPs) == 0:
            return None
        elif len(UPs) == 1:
            return UPs[0].value
        else:
            logging.warning("UserProperty not unique! User: {}, Key: {}".format(self.id, key))
            return None

    def set_property(self, key, value):
        """Sets or updates a goal  property."""
        (p, created) = UserProperty.objects.get_or_create(user=self, key=key)
        p.value = value
        p.save()


class UserProperty(models.Model):
    """
    A UserProperty specifies a User. For example: key=age, value=42
    Permissions to use data are also stored here.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(SiddataUser, on_delete=models.CASCADE, default=None)
    key = models.CharField(max_length=256)
    value = JSONField(null=True)

    def __str__(self):
        """String representation of a UserProperty object."""
        return "UserProperty {}".format(self.key)


class SiddataUserStudy(models.Model):
    """
    Represents one subject for one student:
    Student id, degree, subject and semester. One student can have many SiddataUserStudy entries.
    Examples:
        - Bachelor Informatik, 3. Semester
        - 2-F??cher-Bachelor Latein, 14. Semester
        - Juristisches Staatsexamen Jura, 1. Semester
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    studycourse_origin_id = models.CharField(max_length=512, null=True)
    user = models.ForeignKey(SiddataUser, on_delete=models.CASCADE)  # references entry in SiddataUser table
    degree = models.ForeignKey(Degree, on_delete=models.CASCADE, null=True)  # the prospective degree
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True)  # the subject
    semester = models.IntegerField(null=True)  # the semester for this subject
    share_subject_brain = models.BooleanField(default=False)
    share_subject_social = models.BooleanField(default=False)
    share_degree_brain = models.BooleanField(default=False)
    share_degree_social = models.BooleanField(default=False)
    share_semester_brain = models.BooleanField(default=False)
    share_semester_social = models.BooleanField(default=False)

    def __str__(self):
        """String representation of a SiddataUserStudy object."""
        if self.subject is not None and self.degree is not None:
            return "SiddataUserStudy {} {} {} {}".format(
                self.user.id, self.degree.name, self.subject.name, self.semester
            )
        else:
            return "SiddataUserStudy {} {}".format(self.user.id, self.semester)

    def serialize(self):
        response_data = {
            "data": [
                {
                    "type": "SiddataUserStudy",
                    "id": self.id,
                    "attributes": {
                        "studip_id": self.studycourse_origin_id,
                        "semester": self.semester,
                        "share_subject_brain": self.share_subject_brain,
                        "share_subject_social": self.share_subject_social,
                        "share_degree_brain": self.share_degree_brain,
                        "share_degree_social": self.share_degree_social,
                        "share_semester_brain": self.share_semester_brain,
                        "share_semester_social": self.share_semester_social,
                    },
                    "relationships": {},
                }
            ],
        }
        return response_data


class Recommender(models.Model):
    """
    Represents a recommender
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1024)
    classname = models.CharField(max_length=256)
    description = models.CharField(max_length=2048, null=True)
    image = models.CharField(max_length=256, null=True)
    order = models.IntegerField(null=True)
    data_info = models.CharField(
        max_length=256,
        default="Die bei der Nutzung enstehenden Daten werden auf dem \
               Siddata Server gespeichert.",
    )

    def __str__(self):
        """String representation of a Recommender object."""
        return "Recommender {}".format(self.name)


class SiddataUserRecommender(models.Model):
    """
    Represents the usage of a recommender by a student
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(SiddataUser, on_delete=models.CASCADE)
    recommender = models.ForeignKey(Recommender, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False)

    def __str__(self):
        """String representation of a Category object."""
        return "User {} uses recommender {}".format(self.user.id, self.recommender.name)

    def serialize(self, include=True):
        """
        Converts a Recommender instance related to a certain user to nested structure that can be transformed to JSON.
        Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """

        goal_dicts = []
        included = []
        goals = Goal.objects.filter(userrecommender=self).order_by("order")
        for goal in goals:
            goal_dicts.append({"id": goal.id, "type": "Goal"})
            if include:
                g_ser = goal.serialize(include=True)
                for entry in g_ser["data"] + g_ser["included"]:
                    if entry not in included:
                        included.append(entry)

        response_data = {
            "data": [
                {
                    "type": "Recommender",
                    "id": self.id,
                    "attributes": {
                        "name": self.recommender.name,
                        "classname": self.recommender.classname,
                        "description": self.recommender.description,
                        "image": "{}{}".format(settings.IMAGE_URL, self.recommender.image),
                        "order": self.recommender.order,
                        "enabled": self.enabled,
                        "data_info": self.recommender.data_info,
                    },
                    "relationships": {
                        "goals": {"data": goal_dicts},
                        "activities": {"data": []},
                        "students": {"data": [{"type": "SiddataUser", "id": self.user.id}]},
                    },
                }
            ],
        }

        if include:
            u_ser = self.user.serialize(include=[])["data"][0]
            if u_ser not in included:
                included.append(u_ser)
            response_data["included"] = included

        return response_data


class Goal(models.Model):
    """
    Structure that represents some interest of a student. Has Activities as children.
        attributes:
        type: if type is set to "form" all children will be displayed in the frontend with one submit button.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=1024, null=True)
    description = models.TextField(null=True)
    makedate = models.DateTimeField(auto_now_add=True)
    userrecommender = models.ForeignKey(SiddataUserRecommender, on_delete=models.CASCADE)
    order = models.IntegerField(default=1)
    type = models.CharField(max_length=1024, null=True)
    visible = models.BooleanField(default=True)

    def __str__(self):
        """String representation of a Goal object."""
        return self.title

    def serialize(self, include=True):
        """
        Converts Goal instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """

        included = []

        activity_dicts = []
        activityset = Activity.objects.filter(goal=self).order_by("order")

        for activity in activityset:
            activity_dicts.append({"id": activity.id, "type": "Activity"})
            if include:
                a_ser = activity.serialize()
                for entry in a_ser["data"] + a_ser["included"]:
                    if entry not in included:
                        included.append(entry)

        goalproperty_dicts = []
        goalpropertyset = GoalProperty.objects.filter(goal=self)
        for goalproperty in goalpropertyset:
            goalproperty_dicts.append({"id": goalproperty.id, "type": "GoalProperty"})
            gp_ser = goalproperty.serialize()
            if include:
                for entry in gp_ser["data"] + gp_ser["included"]:
                    if entry not in included:
                        included.append(entry)

        response_data = {
            "data": [
                {
                    "type": "Goal",
                    "id": self.id,
                    "attributes": {
                        "title": self.title,
                        "description": self.description,
                        "makedate": self.makedate,
                        "user": self.userrecommender.user.pk,
                        "recommender": self.userrecommender.recommender.name,
                        "order": self.order,
                        "type": self.type,
                        "visible": self.visible,
                    },
                    "relationships": {
                        "activities": {"data": activity_dicts},
                        "goalproperties": {"data": goalproperty_dicts},
                        "students": {"data": [{"id": self.userrecommender.user.id, "type": "SiddataUser"}]},
                    },
                }
            ],
        }

        if include:
            userrec_ser = self.userrecommender.serialize(include=False)["data"][0]
            if userrec_ser not in included:
                included.append(userrec_ser)
            response_data["included"] = included

        return response_data

    def get_property(self, key):
        """Get a goal's property identified by key.

        This encapsulates the goal property handling with GoalProperty objects.
        :return:The key's value as a string or None if key is not set."""
        GPs = GoalProperty.objects.filter(goal=self, key=key)
        if len(GPs) == 0:
            return None
        elif len(GPs) == 1:
            return GPs[0].value
        else:
            # must not happen: The key is not unique
            logging.warning("GoalProperty not unique! Goal: {} Key: {}".format(self.id, key))

    def set_property(self, key, value):
        """Sets or updates a goal  property."""
        (p, created) = GoalProperty.objects.get_or_create(goal=self, key=key)
        p.value = value
        p.save()


class GoalProperty(models.Model):
    """A GoalProperty specifies a goal. For example: key=country, value=england"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, default=None)
    key = models.CharField(max_length=256)
    value = JSONField(null=True)

    def __str__(self):
        """String representation of a GoalProperty object."""
        return "GoalProperty {}".format(self.key)

    def serialize(self):
        """
        Converts GoalProperty instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [
                {
                    "type": "GoalProperty",
                    "id": self.id,
                    "attributes": {
                        "key": self.key,
                        "value": self.value,
                    },
                }
            ],
            "included": [],
        }
        return response_data


class Category(models.Model):
    """A category of goals, for instance DDC-codes but also the categories from our goal tagset."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=1024)
    super_category = models.ForeignKey("Category", on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        """String representation of a Category object."""
        return "Category {}".format(self.name)


class GoalCategory(models.Model):
    """Represents one goal categorized by majority vote.
    One goal can have many categories and can only once be categorized by the majority vote.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    belongs_to = models.BooleanField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """String representation of a GoalCategory object."""
        return "GoalCategory {} {}".format(self.goal.title, self.category.name)


class EducationalResource(models.Model):
    """Represents an educational resource like books, courses, MOOCs etc."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ddc_code = models.JSONField(null=True)
    origin = models.ForeignKey(Origin, on_delete=models.CASCADE, related_name="educational_resource_origin", null=True)
    TF_IDF_scores = JSONField(null=True)

    # dublin core fields
    contributor = models.JSONField(null=True)
    # time and place string if present
    coverage = models.CharField(max_length=1024, null=True)
    # lom creator or visible instructors
    creator = models.JSONField(null=True)
    date = models.DateTimeField(max_length=128, null=True)
    description = models.TextField(null=True)
    # pdf/video/mooc/etc.
    format = models.JSONField(max_length=1024, null=True)
    language = LanguageField(max_length=1024, null=True)
    publisher = models.CharField(max_length=1024, null=True)  # keep it None for now, later maybe alias with origin
    relation = models.CharField(max_length=1024, null=True)
    rights = models.CharField(max_length=1024, null=True)
    # URL to original resource
    source = models.CharField(max_length=1024, null=True)
    # list of content-related keywords
    subject = models.JSONField(null=True)
    title = models.CharField(max_length=1024)
    # list of type-related keywords
    type = models.JSONField(null=True)

    def serialize(self):
        """
        Converts EducationalResource instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [
                {
                    "type": "EducationalResource",
                    "id": self.id,
                    "attributes": {
                        "title": self.title,
                        "description": self.description,
                        "url": self.source,
                    },
                }
            ],
            "included": [],
        }
        return response_data


class InheritingCourse(EducationalResource):
    course_origin_id = models.CharField(max_length=512, default=None)

    def __str__(self):
        """String representation of an Event object."""
        return f"{type(self).__name__} {self.title}"

    def serialize(self):
        """
        Converts Course instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [
                {
                    "type": "Course",
                    "id": self.id,
                    "attributes": {
                        "title": self.title,
                        "description": self.description,
                        "url": self.source,
                        "origin_id": self.course_origin_id,
                    },
                }
            ],
            "included": [],
        }
        return response_data


class StudipCourse(InheritingCourse):
    place = models.CharField(max_length=1024, null=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    start_semester = models.CharField(max_length=128)
    end_semester = models.CharField(max_length=128)

    def serialize(self):
        """
        Converts Course instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [
                {
                    "type": "Course",
                    "id": self.id,
                    "attributes": {
                        "title": self.title,
                        "description": self.description,
                        "place": self.place,
                        "start_time": datetime.datetime.timestamp(self.start_time),
                        "end_time": datetime.datetime.timestamp(self.end_time),
                        "start_semester": self.start_semester,
                        "end_semester": self.end_semester,
                        "url": self.source,
                        "studip_id": self.course_origin_id,
                    },
                }
            ],
            "included": [],
        }
        return response_data


class InheritingEvent(EducationalResource):
    course = models.ForeignKey(InheritingCourse, on_delete=models.CASCADE, null=True)
    event_origin_id = models.CharField(max_length=128)

    def __str__(self):
        """String representation of an Event object."""
        return f"{type(self).__name__} {self.title}"

    def serialize(self):
        """
        Converts an Event instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [
                {
                    "type": "Event",
                    "id": self.id,
                    "attributes": {
                        "title": self.title,
                        "description": self.description,
                        "origin_id": self.event_origin_id,
                        "type": self.type,
                        "self": (self.course.id if self.course else self.course),
                        "url": self.source,
                        "origin": self.origin.name,
                        "ddc_code": self.ddc_code,
                    },
                }
            ],
            "included": [self.course],
        }

        return response_data


class StudipEvent(InheritingEvent):
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    place = models.CharField(max_length=1024)

    def serialize(self):
        """
        Converts an Event instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [
                {
                    "type": "Event",
                    "id": self.id,
                    "attributes": {
                        "title": self.title,
                        "description": self.description,
                        "studip_id": self.event_origin_id,
                        "start_time": datetime.datetime.timestamp(self.start_time),
                        "end_time": datetime.datetime.timestamp(self.end_time),
                        "type": self.type,
                        "self": (self.course.id if self.course else self.course),
                        "url": self.source,
                        "place": self.place,
                        "origin": self.origin.name,
                        "ddc_code": self.ddc_code,
                    },
                }
            ],
            "included": [self.course],
        }

        return response_data


class WebResource(EducationalResource):
    iframe = models.BooleanField(default=False)

    def __str__(self):
        """String representation of a Resource object."""
        return f"{type(self).__name__} {self.title}"

    def serialize(self):
        """
        Converts Resource instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [
                {
                    "type": "Resource",
                    "id": self.id,
                    "attributes": {
                        "title": self.title,
                        "description": self.description,
                        "url": self.source,
                        "iframe": self.iframe,
                        "origin": [self.origin.name if self.origin else None],
                    },
                }
            ],
            "included": [],
        }
        return response_data


class Question(models.Model):
    """Represents a question"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question_text = models.TextField()
    answer_type = models.CharField(max_length=1024)
    selection_answers = ArrayField(models.CharField(max_length=256), null=True)

    def __str__(self):
        """String representation of an Question object."""
        return "Question {}".format(self.question_text)

    def serialize(self):
        """
        Converts Question instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [
                {
                    "type": "Question",
                    "id": self.id,
                    "attributes": {
                        "question_text": self.question_text,
                        "answer_type": self.answer_type,
                        "selection_answers": self.selection_answers,
                    },
                }
            ],
            "included": [],
        }
        return response_data


class Person(models.Model):
    """Represents a person"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.CharField(max_length=256, null=True)
    first_name = models.CharField(max_length=256)
    second_name = models.CharField(max_length=256)
    title = models.CharField(max_length=256)
    email = models.CharField(max_length=256)
    role_description = models.TextField(null=True)
    url = models.CharField(max_length=256)

    def __str__(self):
        """String representation of an Question object."""
        return "Person {} {}".format(self.first_name, self.second_name)

    def serialize(self):
        """
        Converts Question instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """
        response_data = {
            "data": [
                {
                    "type": "person",
                    "id": self.id,
                    "attributes": {
                        "image": self.image,
                        "first_name": self.first_name,
                        "second_name": self.second_name,
                        "title": self.title,
                        "email": self.email,
                        "role_description": self.role_description,
                        "url": self.url,
                    },
                }
            ],
            "included": [],
        }
        return response_data


class Activity(models.Model):
    """Represents an activity
    attributes:
        order:  According to this integer the frontend will order the activities in a goal.
                structure: 1xxxyyyzzz
                            xxx high
                            yyy medium
                            zzz fine
        status: new(freshly created)
                active(active (again?)
                snoozed(student wants to postpone it)
                discarded(student has disabled it)
                done(whohooo!)
        type:   todo (standalone activity),
                resource(displays a Resource object, reference in resource attribute required)
                course(displays a Course object, reference in course attribute required) ,
                event(displays an Event object, reference in event attribute required)
                question(displays a Question object, reference in question attribute required)
                person(dispalys a Person object, reference in person attribute required)
        activation_time: activity will only be shown after this date (f.i. reminder)
        deactivation_time: activity will only be shown until this date (f.i. event recommendation)
        color_theme: defines a color (red, green, yellow)
        button_text: defines a text which is displayed on the submit button in the frontend
        template_ref: template to which the activity refers
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=1024, null=True)
    description = models.TextField(null=True)
    type = models.CharField(max_length=1024)
    status = models.CharField(max_length=1024)
    course = models.ForeignKey(InheritingCourse, on_delete=models.CASCADE, null=True)
    event = models.ForeignKey(InheritingEvent, on_delete=models.CASCADE, null=True)
    resource = models.ForeignKey(WebResource, on_delete=models.CASCADE, null=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True)
    answers = ArrayField(models.CharField(max_length=256), null=True, default=list)
    feedback_size = models.IntegerField(default=4)
    feedback_value = models.IntegerField(null=True)
    feedback_text = models.CharField(max_length=1024, null=True)
    feedback_chdate = models.DateTimeField(null=True)
    notes = models.CharField(max_length=1024, null=True)
    duedate = models.DateTimeField(null=True)
    order = models.IntegerField(null=True)
    chdate = models.DateTimeField(null=True)
    mkdate = models.DateTimeField(auto_now_add=True)
    activation_time = models.DateTimeField(null=True)
    deactivation_time = models.DateTimeField(null=True)
    image = models.CharField(max_length=256, null=True)
    color_theme = models.CharField(max_length=256, null=True)
    button_text = models.CharField(max_length=128, null=True)
    template_ref = models.ForeignKey("ActivityTemplate", on_delete=models.CASCADE, null=True)

    def __str__(self):
        """String representation of an Activity object."""
        return "Activity {} {}".format(self.title, self.description)

    def get_dynamic_attributes(self):
        """
        Attributes which should get dynamically from template.
        Dynamic attributes always prioritize non empty Template attributes against Activity attributes.
        """
        return [
            "title",
            "description",
            "type",
            "course",
            "event",
            "resource",
            "question",
            "person",
            "feedback_size",
            "notes",
            "duedate",
            "order",
            "image",
            "button_text",
        ]

    def __getattribute__(self, item):
        """
        Implements prioritize mechanism for ActivityTemplate attributes.
        Return Activity attribute if corresponding TemplateActivity attribute is not set (empty|null).
        """
        # Prioritize template attribute only if it is a dynamic attribute
        if item in object.__getattribute__(self, "get_dynamic_attributes")():
            # if template reference not exist
            if not object.__getattribute__(self, "template_ref_id"):
                # return Activity attribute
                return object.__getattribute__(self, item)

            template_item = getattr(object.__getattribute__(self, "template_ref"), item)
            # if template attribute is set
            if template_item:
                # return Template attribute
                return template_item
            else:
                return object.__getattribute__(self, item)
        # return Activity attribute
        return object.__getattribute__(self, item)

    @staticmethod
    def create_activity_from_template(template_id, goal, status="new", **kwargs):
        """
        Creates an activity instance from a specific template
        """

        template = ActivityTemplate.objects.get(template_id=template_id)

        attributes = {}
        # copy all Template attributes which are specified as dynamic
        for attribute in template.get_dynamic_attributes():
            attributes[attribute] = getattr(template, attribute)

        attributes["goal"] = goal
        attributes["status"] = status
        attributes["template_ref"] = template

        # create activity
        activity = Activity.objects.get_or_create(**attributes)[0]

        # allow setting of values different from template
        for field, value in kwargs.items():
            setattr(activity, field, value)

        activity.save()

        return activity

    def has_template(self, template_id):
        """
        Returns true if the passed template_id matches the containing template reference
        """
        return self.template_ref_id == template_id

    def serialize(self, include=True):
        """
        Converts an Activity instance to nested structure that can be transformed to JSON. Follows REST API standards at
        https://jsonapi.org.
        :return: data Dictionary with nested data.
        """

        # Do not return Activity if it is not active yet or not active anymore
        now = datetime.datetime.now()
        start = datetime.datetime.timestamp(self.activation_time) if self.activation_time else None
        end = datetime.datetime.timestamp(self.deactivation_time) if self.deactivation_time else None
        if start and end and (now < start or now > end):
            return None

        response_data = {
            "data": [
                {
                    "type": "Activity",
                    "id": self.id,
                    "attributes": {
                        "description": self.description,
                        "type": self.type,
                        "goal_id": self.goal.pk,
                        "title": self.title,
                        "status": self.status,
                        "answers": self.answers,
                        "feedback_size": self.feedback_size,
                        "feedback_value": self.feedback_value,
                        "feedback_text": self.feedback_text,
                        "feedback_chdate": self.feedback_chdate,
                        "notes": self.notes,
                        "duedate": self.duedate,
                        "order": self.order,
                        "chdate": self.chdate,
                        "mkdate": self.mkdate,
                        "activation_time": self.activation_time,
                        "deactivation_time": self.deactivation_time,
                        "image": "{}{}".format(settings.IMAGE_URL, self.image),
                        "color_theme": self.color_theme,
                        "button_text": self.button_text,
                    },
                    "relationships": {
                        "course": {"data": [{"id": self.course.id, "type": "Course"}] if self.course else []},
                        "resource": {"data": [{"id": self.resource.id, "type": "Resource"}] if self.resource else []},
                        "question": {"data": [{"id": self.question.id, "type": "Question"}] if self.question else []},
                        "event": {"data": [{"id": self.event.id, "type": "Event"}] if self.event else []},
                    },
                }
            ],
        }

        if include:
            included = []
            serialized = []
            if self.course:
                cs = self.course.serialize()
                serialized += cs["data"] + cs["included"]
            if self.resource:
                rs = self.resource.serialize()
                serialized += rs["data"] + rs["included"]
            if self.question:
                qs = self.question.serialize()
                serialized += qs["data"] + qs["included"]
            if self.event:
                es = self.event.serialize()
                serialized += es["data"] + es["included"]

            for entry in serialized:
                if entry not in included:
                    included.append(entry)

            userrec_ser = self.goal.userrecommender.serialize(include=False)["data"][0]
            if userrec_ser not in included:
                included.append(userrec_ser)
            goal_ser = self.goal.serialize(include=False)["data"][0]
            if goal_ser not in included:
                included.append(goal_ser)
            user_ser = self.goal.userrecommender.user.serialize(include=[])["data"][0]
            if user_ser not in included:
                included.append(user_ser)

            response_data["included"] = included

        return response_data


class ActivityTemplate(Activity):
    """Represents an activity template

    Basic usage:
        Below is explained how a template and an activity from a template could be created and
        how the template id could be used in conditions (e.g. in process_activity).
        For more information see backend wiki.

        Creating Templates:
            Templates need to be defined in the "initialize_templates(self)" function of a recommender.
            A Template is created like an activity and contains dynamic attributes which are used for
            all activities of this template. If a dynamic attribute is not set the activity uses his own attribute
            which is set in the activity creating function. In addition the status of a template is "template" to make
            templates distinguishable from activities.

            In a recommender each template must have an unique template id. An unique id is get by
            "get_template_id(self, template_name, origin=None)". Template name or pair of template name and origin
            must be unique. Otherwise a template couldn't clearly identified in the
            "activity_create_from_template" function.


            Example:
            def initialize_templates(self):

                super().initialize_templates()                          # creates the teaser template

                sid_question = models.Question.objects.get_or_create(
                    question_text="Hallo, ich bin Sid und gebe dir ein paar Tipps f??r den Einstieg in den Siddata "
                                  "Studienassistenten. ",
                    answer_type="selection",
                    selection_answers=["Ich m??chte alles genau wissen",
                                       "Die Basics bitte",
                                       "Keine Tipps"]
                )[0]

                models.ActivityTemplate.objects.update_or_create(
                    template_id=self.get_template_id("welcome"),        # unique template id
                    defaults={                                          # contains dynamic attributes
                        "title": "Herzlich willkommen",
                        "type": "question",
                        "question": sid_question,
                        "status": "template",                           # template status
                        "image": "sid.png",
                        "feedback_size": 0,
                        "order": 1000000001,
                    }
                )

        Creating Activities:
            Activities are created by using the following function:
                "create_activity_from_template(template_id, goal, status="new", **kwargs)"

            The template id must match with the id of an existing template. A goal must be assigned for each activity.
            The kwargs parameter allows setting of values which will be assigned to the activity and could be
            different from template (e.g. title).

            Example:
                models.Activity.create_activity_from_template(
                    template_id=self.get_template_id("welcome"),
                    goal=goal,
                )

        Conditions with template id:
            The activity model contains a method called "has_template(self, template_id)" which checks
            if the template id matches the containing template of an activity. This function could be used for
            the processing of an activity.

            Example:
                if activity.has_template(self.get_template_id("welcome")):
                    # do something with this activity
    """

    template_id = models.CharField(max_length=256, primary_key=True)
    activity_ptr = models.OneToOneField(
        Activity,
        on_delete=models.CASCADE,
        parent_link=True,
    )


class RequestLog(models.Model):
    """Represents a Request. For evaluation purposes"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recommender = models.ForeignKey(Recommender, on_delete=models.CASCADE, null=True)
    user = models.ForeignKey(SiddataUser, on_delete=models.CASCADE, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    route = models.CharField(max_length=1024)


class CourseMembership(models.Model):
    """Course Enrollment"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(SiddataUser, on_delete=models.CASCADE, null=True)
    course = models.ForeignKey(StudipCourse, on_delete=models.CASCADE, null=True)
    share_brain = models.BooleanField(default=False)
    share_social = models.BooleanField(default=False)


class Institute(models.Model):
    """Represents University Institutes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=512)
    url = models.CharField(max_length=512, null=True)
    origin = models.ForeignKey(Origin, on_delete=models.CASCADE)
    institute_origin_id = models.CharField(max_length=512)


class InstituteMembership(models.Model):
    """Institute affiliation"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(SiddataUser, on_delete=models.CASCADE, null=True)
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, null=True)
    share_brain = models.BooleanField(default=False)
    share_social = models.BooleanField(default=False)
