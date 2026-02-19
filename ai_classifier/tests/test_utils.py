"""
Test per file handlers e validators
"""
import pytest
from ai_classifier.utils.file_handlers import FileTypeDetector, PathValidator
from ai_classifier.utils.validators import ClassificationValidator, ConfigValidator


class TestFileTypeDetector:
    """Test FileTypeDetector"""
    
    def test_is_supported_file_pdf(self):
        """Test verifica file PDF supportato"""
        assert FileTypeDetector.is_supported_file('test.pdf')
        assert FileTypeDetector.is_supported_file('test.PDF')
    
    def test_is_supported_file_image(self):
        """Test verifica immagini supportate"""
        assert FileTypeDetector.is_supported_file('test.jpg')
        assert FileTypeDetector.is_supported_file('test.png')
    
    def test_is_unsupported_file(self):
        """Test verifica file non supportato"""
        assert not FileTypeDetector.is_supported_file('test.exe')
        assert not FileTypeDetector.is_supported_file('test.txt')


class TestPathValidator:
    """Test PathValidator"""
    
    def test_normalize_path(self):
        """Test normalizzazione path"""
        path = PathValidator.normalize_path('/tmp/../test')
        assert '..' not in path
    
    def test_is_network_path_unc(self):
        """Test riconoscimento UNC path"""
        assert PathValidator.is_network_path('\\\\server\\share')
        assert PathValidator.is_network_path('//server/share')
    
    def test_is_not_network_path(self):
        """Test path locale"""
        assert not PathValidator.is_network_path('/tmp/test')


class TestClassificationValidator:
    """Test ClassificationValidator"""
    
    def test_validate_classification_result_valid(self):
        """Test validazione risultato valido"""
        result = ClassificationValidator.validate_classification_result(
            predicted_type='CED',
            confidence_score=0.85
        )
        
        assert result['valid']
        assert result['confidence_level'] == 'high'
    
    def test_validate_classification_result_invalid_type(self):
        """Test validazione tipo invalido"""
        with pytest.raises(ValueError):
            ClassificationValidator.validate_classification_result(
                predicted_type='INVALID',
                confidence_score=0.85
            )
    
    def test_validate_classification_result_invalid_score(self):
        """Test validazione score invalido"""
        with pytest.raises(ValueError):
            ClassificationValidator.validate_classification_result(
                predicted_type='CED',
                confidence_score=1.5
            )
    
    def test_calculate_confidence_level(self):
        """Test calcolo livello confidenza"""
        assert ClassificationValidator.calculate_confidence_level(0.9) == 'high'
        assert ClassificationValidator.calculate_confidence_level(0.6) == 'medium'
        assert ClassificationValidator.calculate_confidence_level(0.3) == 'low'


class TestConfigValidator:
    """Test ConfigValidator"""
    
    def test_validate_llm_config_valid(self):
        """Test validazione config LLM valida"""
        config = ConfigValidator.validate_llm_config(
            provider='openai',
            model='gpt-4o-mini',
            temperature=0.1,
            max_tokens=500
        )
        
        assert config['valid']
    
    def test_validate_llm_config_invalid_provider(self):
        """Test validazione provider invalido"""
        with pytest.raises(ValueError):
            ConfigValidator.validate_llm_config(
                provider='invalid',
                model='gpt-4',
                temperature=0.1,
                max_tokens=500
            )
    
    def test_validate_patterns_valid(self):
        """Test validazione pattern validi"""
        patterns = {
            'CED': ['cedolino', 'payslip'],
            'UNI': ['unilav']
        }
        
        assert ConfigValidator.validate_patterns(patterns)
    
    def test_validate_patterns_invalid(self):
        """Test validazione pattern invalidi"""
        patterns = {
            'INVALID_TYPE': ['pattern']
        }
        
        assert not ConfigValidator.validate_patterns(patterns)
