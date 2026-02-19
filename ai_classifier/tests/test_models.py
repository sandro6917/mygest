"""
Test base per AI Classifier
"""
import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker
from ai_classifier.models import ClassificationJob, ClassificationResult, ClassifierConfig

User = get_user_model()


@pytest.mark.django_db
class TestClassificationJob:
    """Test ClassificationJob model"""
    
    def test_create_job(self):
        """Test creazione job"""
        user = baker.make(User)
        job = ClassificationJob.objects.create(
            directory_path='/tmp/test',
            created_by=user
        )
        
        assert job.status == 'pending'
        assert job.total_files == 0
        assert job.processed_files == 0
    
    def test_start_job(self):
        """Test avvio job"""
        user = baker.make(User)
        job = ClassificationJob.objects.create(
            directory_path='/tmp/test',
            created_by=user
        )
        
        job.start()
        
        assert job.status == 'running'
        assert job.started_at is not None
    
    def test_complete_job(self):
        """Test completamento job"""
        user = baker.make(User)
        job = ClassificationJob.objects.create(
            directory_path='/tmp/test',
            created_by=user,
            status='running'
        )
        
        job.complete()
        
        assert job.status == 'completed'
        assert job.completed_at is not None


@pytest.mark.django_db
class TestClassificationResult:
    """Test ClassificationResult model"""
    
    def test_create_result(self):
        """Test creazione result"""
        user = baker.make(User)
        job = baker.make(ClassificationJob, created_by=user)
        
        result = ClassificationResult.objects.create(
            job=job,
            file_path='/tmp/test.pdf',
            file_name='test.pdf',
            file_size=1024,
            mime_type='application/pdf',
            predicted_type='CED',
            confidence_score=0.85,
            confidence_level='high',
            classification_method='rule'
        )
        
        assert result.predicted_type == 'CED'
        assert result.confidence_score == 0.85
        assert not result.imported


@pytest.mark.django_db
class TestClassifierConfig:
    """Test ClassifierConfig model"""
    
    def test_get_config_singleton(self):
        """Test singleton pattern"""
        config1 = ClassifierConfig.get_config()
        config2 = ClassifierConfig.get_config()
        
        assert config1.id == config2.id
        assert ClassifierConfig.objects.count() == 1
    
    def test_default_patterns(self):
        """Test pattern di default"""
        config = ClassifierConfig.get_config()
        
        assert 'CED' in config.filename_patterns
        assert 'cedolino' in config.filename_patterns['CED']
        assert 'UNI' in config.content_patterns
