import json
from os.path import abspath, basename, dirname, isdir, isfile, join, split, splitext

import numpy as np
import pandas as pd
import requests
import transformers
from django.conf import settings


class BertPredictor:
    max_length = 300
    top_n = 1

    def __init__(self):
        self.file_path = join(settings.BASE_DIR, "data", "Sidbert")
        self.classes = self._load_classes_from_tsv(join(self.file_path, "bert_data", "classes.tsv"))
        # create label lookup table for label assignment from last classification layer
        self.sparse_label_codes = self._create_sparse_label_lookup()
        self.tokenizer = transformers.BertTokenizer.from_pretrained("bert-base-multilingual-cased")

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
        model_url = "http://localhost:8501/v1/models/fashion_model:predict"
        input = self.preprocess(input)
        output = self.call_model(model_url, input)
        output = self.postprocess(output)
        return output


if __name__ == "__main__":
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.development")
    predictor = BertPredictor()

    result = predictor.predict("Machine Learning")
    print(result)
