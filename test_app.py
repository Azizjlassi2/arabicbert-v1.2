import unittest
from unittest.mock import patch
from model import (  
    simulate_text_classification,
    simulate_ner,
    simulate_sentiment_analysis,
    simulate_question_answering,
    app  
)
from flask import json

class TestArabicBERTSimulation(unittest.TestCase):

    def test_text_classification(self):
        """Test de classification thématique pour cas nominaux et par défaut."""
        # Cas sport
        result = simulate_text_classification("الفريق التونسي فاز بالبطولة الأفريقية")
        self.assertEqual(result["category"], "sport")
        
        
        # Cas santé
        result = simulate_text_classification("أعلنت وزارة الصحة عن إصابات جديدة بكورونا")
        self.assertEqual(result["category"], "santé")
        
        
        # Cas politique (nouveau)
        result = simulate_text_classification("أعلن الرئيس عن إصلاحات حكومية جديدة")
        self.assertEqual(result["category"], "politique")
        
        
        # Cas par défaut
        result = simulate_text_classification("نص عام بدون thèmes spécifiques")
        self.assertEqual(result["category"], "general")
        

    def test_ner(self):
        """Test de reconnaissance d'entités nommées pour types étendus."""
        text = "زار الرئيس قيس سعيد مدينة صفاقس يوم الجمعة للقاء رئيس البلدية"
        
        result = simulate_ner(text)
        expected_entities = [
        {
            "end": 19,
            "entity": "قيس سعيد",
            "start": 11,
            "type": "PER"
        },
        {
            "end": 31,
            "entity": "صفاقس",
            "start": 26,
            "type": "LOC"
        }
          
        ]
        self.assertEqual(len(result), len(expected_entities))
        for i, ent in enumerate(result):
            self.assertEqual(ent["entity"], expected_entities[i]["entity"])
            self.assertEqual(ent["type"], expected_entities[i]["type"])

    def test_sentiment_analysis(self):
        """Test d'analyse de sentiment avec pondération et variantes linguistiques."""
        # Cas positif standard
        result = simulate_sentiment_analysis("الخدمة كانت ممتازة والموظفون متعاونون")
        self.assertEqual(result["sentiment"], "positive")
        
        self.assertEqual(result["label"], "إيجابي")
        
        # Cas négatif dialectal
        result = simulate_sentiment_analysis("والله ما عجبنيش الفيلم، كان ممل برشا", language="tn")
        self.assertEqual(result["sentiment"], "negative")
        
        self.assertEqual(result["label"], "سلبي")
        
        # Cas neutre avec pondération
        result = simulate_sentiment_analysis("الأمر عادي ومقبول جزئيا")
        self.assertEqual(result["sentiment"], "neutral")
        

    def test_question_answering(self):
        """Test de QA extractive pour patterns enrichis."""
        context = "تونس بلد يقع في شمال أفريقيا. عاصمتها مدينة تونس وعدد سكانها حوالي 12 مليون نسمة. في عام 1956 حصلت تونس على استقلالها بقيادة الحبيب بورقيبة."
        
        # Cas capitale
        result = simulate_question_answering(context, "ما هي عاصمة تونس؟")
        
        
        
        # Cas indépendance
        result = simulate_question_answering(context, "متى حصلت تونس على استقلالها؟")
        self.assertEqual(result["answer"], "1956")
        
        
        # Cas population (nouveau)
        result = simulate_question_answering(context, "ما هو عدد سكان تونس؟")
        self.assertEqual(result["answer"], "12 مليون")
        
        # Cas localisation (nouveau)
        result = simulate_question_answering(context, "أين تقع تونس؟")
        self.assertEqual(result["answer"], "شمال أفريقيا")
        
        # Cas sans réponse
        result = simulate_question_answering(context, "ما هو le nom du chat du président ?")
        self.assertEqual(result["answer"], "")
        

    @patch('model.authenticate')  
    def test_predict_endpoint(self, mock_auth):
        mock_auth.return_value = None  # Simule une authentification réussie
        
        # Test classification via endpoint
        with app.test_client() as client:
            response = client.post('/v1/models/arabicbert/predict',
                                   json={"task": "text_classification", "input": "مباراة رياضية مثيرة"},
                                   content_type='application/json')
            data = json.loads(response.data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["result"]["category"], "sport")
            self.assertIn("processing_time_ms", data["metadata"])
        
        # Test tâche non supportée
        with app.test_client() as client:
            response = client.post('/v1/models/arabicbert/predict',
                                   json={"task": "invalid_task"},
                                   content_type='application/json')
            self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()