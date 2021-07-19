import json
import logging
import os
from datetime import date, datetime, timedelta
from os.path import join

import numpy as np
import pandas as pd
import requests
from django.conf import settings
from django.db.models import Q

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # make tensorflow shut up
import transformers  # noqa: 402

from apps.backend import models  # noqa: 402


def check_current_semester():
    year, month = datetime.today().year, datetime.today().month
    if month in range(4, 10):  # This assumes that semesters always start on October 1st and April 1st.
        start_date = date(year, 3, 31)
    elif month < 4:
        start_date = date(year - 1, 9, 30)
    elif month > 9:
        start_date = date(year, 9, 30)
    return start_date


class BertPredictor:
    max_length = 300
    top_n = 1

    def __init__(self):
        self.model_url = settings.TF_SERVING_BASE_URL + "rm_professions:predict"
        self.file_path = join(settings.BASE_DIR, "data", "RM_professions")
        self.classes = self._load_classes_from_tsv(join(self.file_path, "classes.tsv"))
        # create label lookup table for label assignment from last classification layer
        self.sparse_label_codes = self._create_sparse_label_lookup()
        self.tokenizer = transformers.BertTokenizerFast.from_pretrained("bert-base-multilingual-cased")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("BertPredictor initialized.")

    def _load_classes_from_tsv(self, class_path):
        """
        loads all label IDs from the classes.tsv file
        returns: pandas dataframe object containing all label identities.
        """
        classes_frame = pd.read_csv(class_path, delimiter="\t", names=["DDC"], dtype=str)
        return classes_frame["DDC"].values.tolist()

    def _create_sparse_label_lookup(self):
        """
        creates a dictionary for label lookup. As output neurons from the network do not posess an inherent label,
        a lookup must be performed to assess the ddc class an input was associated with.
        """
        return {self.classes[index]: index for index in range(len(self.classes))}

    def preprocess(self, input: str):
        """
        Gets the string as input and returns what will be the input to the ANN/Model
        """
        encoded_sequence = self.tokenizer.encode_plus(
            input,
            add_special_tokens=True,
            padding="max_length",
            max_length=self.max_length,
            truncation=True,
            return_attention_mask=True,
            return_token_type_ids=True,
            pad_to_max_length=True,
            return_tensors="tf",
        )
        instances = {
            "input_token": encoded_sequence["input_ids"].numpy().tolist(),
            "attention_mask": encoded_sequence["attention_mask"].numpy().tolist(),
            "token_type_ids": encoded_sequence["token_type_ids"].numpy().tolist(),
        }
        return instances

    def call_model(self, model_url, processed_input):
        headers = {"content-type": "application/json"}
        data = json.dumps({"signature_name": "serving_default", "inputs": processed_input})
        json_response = requests.post(model_url, data=data, headers=headers)
        if json_response.status_code != 200:
            print(json_response.json()["error"])
            raise Exception
        return np.array(json_response.json()["outputs"][0])

    def postprocess(self, prediction_result):
        max_classes = prediction_result.argsort()[::-1][: self.top_n]
        label_probability_assoc = {}
        for entry in max_classes:
            none_found = True
            for key in predictor.sparse_label_codes.keys():
                if predictor.sparse_label_codes[key] == entry:
                    computed_label = key
                    none_found = False
                    break
            if not none_found:
                label_probability_assoc[str(computed_label)] = str(prediction_result[entry])
        return label_probability_assoc

    def predict(self, input):
        input = self.preprocess(input)
        output = self.call_model(self.model_url, input)
        output = self.postprocess(output)
        return output


class BertBackbone:
    def __init__(self, max_courses=10):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.predictor = BertPredictor()
        self.max_courses = max_courses

    def set_new_semester(self):
        self.current_semester = check_current_semester()
        next_sem = self.current_semester + timedelta(weeks=26)
        self.next_semester = date(next_sem.year, next_sem.month + 1, 1) - timedelta(days=1)

    def generate_sidbert_resources(self, ddc_mapping, filter_tags=None, origin=None, amount=None):
        """
        Generates a list of Course type object that match the DDC codes obtained from SIDBERT
        if no or too little courses exist, a semantic search for nearest courses is conducted.
        :param ddc_mapping: DDC label generated from an input string
        :param origin: origin object that constraints search to local university resources.
        :param filter_tags: list of tag words which resources can be filtered by
        :param amount: number of resources to generate
        You may want to remove this in the future, in case Courses from other universities become available
        """
        matching_resources = []
        self.set_new_semester()
        amount = amount or self.max_courses

        # prepare query of active courses for filtering courses by time
        active_courses = models.StudipCourse.objects.filter(
            Q(ddc_code__icontains='"' + ddc_mapping),
            (Q(start_time__gte=self.current_semester) & Q(start_time__lt=self.next_semester))
            | Q(start_time__gte=self.next_semester),
        )

        # label filter
        qs = Q(ddc_code__icontains='"' + ddc_mapping)

        # filter by tags
        if filter_tags:

            # foreign and local Stud.IP courses
            if origin:
                if "local_course" in filter_tags and "foreign_course" not in filter_tags:
                    # only take local courses
                    qs &= Q(origin=origin)
                elif "foreign_course" in filter_tags and "local_course" not in filter_tags:
                    # only take foreign courses
                    qs &= ~Q(origin=origin)
                # else take both

            # filter by tag words directly
            # "If at least one of the tag words is in the type list, take the object."
            filter_q = Q()
            for tag in filter_tags:
                filter_q |= Q(type__contains=tag)
            qs &= filter_q

        # filter course objects by being active
        qs &= (
            Q(inheritingcourse__isnull=True)
            | Q(inheritingcourse__studipcourse__isnull=True)
            | Q(inheritingcourse__studipcourse__in=active_courses)
        )

        # perform query
        matching_resources += models.EducationalResource.objects.filter(qs)

        if len(matching_resources) > amount:
            matching_resources = matching_resources[:amount]

        if len(matching_resources) < amount:
            threshold = amount - len(matching_resources)
            # TODO: rework this method to find all types of resources
            matching_resources += self.find_closest_ddc_course([(ddc_mapping, 1)], threshold, origin)

        # filtering out recommendations for the same course
        matching_resources = list(set(matching_resources))
        return matching_resources

    def find_closest_ddc_course(self, ddc_label_list, threshold, origin):
        """
        Searches the database for courses with a similar label to the ones given in the input list.
        Similarity here is defined as a number of steps along the DDC graph to get from the originally assigned label
        to the next label with an entry associated with it.
        :param ddc_label_list: List of DDC labels that have been searched already
        :param threshold: Number of courses that need to be found
        :param origin: origin object that constraints search to local university resources.
        You may want to remove this in the future, in case Courses from other universities become available
        """
        new_matching = []
        self.set_new_semester()
        for label, probability in ddc_label_list:
            matching_courses = []
            for index in range(len(label) - 2):
                logging.info("Looking for labels beyond original: " + label)
                label = label[:-1]
                matching_courses += models.StudipCourse.objects.filter(
                    Q(ddc_code__icontains='"' + label),
                    Q(origin=origin),
                    (Q(start_time__gte=self.current_semester) & Q(start_time__lt=self.next_semester))
                    | Q(start_time__gte=self.next_semester),
                )
                matching_courses += models.InheritingCourse.objects.filter(
                    ddc_code__icontains='"' + label, type__contains="MOOC"
                )
                if len(matching_courses) + len(new_matching) >= threshold:
                    new_matching += matching_courses
                    new_matching = new_matching[:threshold]
                    return new_matching
            new_matching += matching_courses
        return new_matching

    def fetch_resources_sidbert(self, goal, origin, filter_tags=None):
        ddc_mapping = self.predictor.predict(goal)
        ddc_label = max([key for key, val in ddc_mapping.items()], key=lambda x: x[1])
        logging.info(f"goal: {goal} was classified as: {ddc_label}")
        sidbert_resources = self.generate_sidbert_resources(ddc_label, origin=origin, filter_tags=filter_tags)
        logging.info(f"Resources generated: \n {sidbert_resources}")
        return sidbert_resources


if __name__ == "__main__":
    # The way it's done here is only for testing/debugging, in production (and also if you're not explicitly testing
    # tf-models), there is a docker-container instead!!
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.development")
    from contextlib import nullcontext

    from apps.backend.util.tf_model_server import TFModelServer

    goal = "Machine Learning"
    with (
        TFModelServer(8501, "rm_professions", model_base_path=settings.BASE_DIR / "data" / "RM_professions")
        if settings.TF_SERVING_HOST == "localhost"
        else nullcontext()
    ):
        predictor = BertPredictor()
        print(predictor.predict(goal))

        backbone = BertBackbone()
        backbone.fetch_resources_sidbert(goal, None)
