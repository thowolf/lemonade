"""Unit tests for NPUMonitor class."""
import pytest
from unittest.mock import patch, MagicMock
from scripts.benchmarks.continue_testing.utils.npu_monitor import NPUMonitor


def test_npu_monitor_sample_npu():
    """Test NPUMonitor.sample_npu() with mocked xrt-smi output."""
    monitor = NPUMonitor()
    
    # Mock subprocess.run and temp file operations
    mock_xrt_output = '''{
        "system": {"xrt": {"version": "2.19.0"}},
        "devices": [{
            "device_id": "0",
            "aie_partitions": {
                "partitions": [{
                    "partition_id": "0",
                    "hw_contexts": [{
                        "context_id": "0",
                        "pid": "1234",
                        "instr_bo_mem": "4096 KB",
                        "command_submissions": 100,
                        "command_completions": 100,
                        "gops": 50.0,
                        "status": "Idle"
                    }]
                }]
            }
        }]
    }'''
    
    with patch('subprocess.run') as mock_run, \
         patch('tempfile.NamedTemporaryFile') as mock_temp:
        
        # Setup mocks
        mock_proc = MagicMock()
        mock_proc.stdout = mock_xrt_output
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc
        
        mock_temp_file = MagicMock()
        mock_temp_file.name = '/tmp/test.json'
        mock_temp.return_value.__enter__.return_value = mock_temp_file
        
        # Test the method
        result = monitor.sample_npu()
        
        assert result["device_count"] == 1
        assert result["instr_bo_kb"] == 4096
        assert result["command_submissions"] == 100
        assert result["command_completions"] == 100
        assert result["utilization_percent"] == 100.0  # All commands completed
        assert result["gops"] == 50.0
        assert len(result["contexts"]) == 1


def test_npu_monitor_parse_xrt_json():
    """Test NPUMonitor.parse_xrt_json() with sample data."""
    monitor = NPUMonitor()
    
    json_data = {
        "devices": [{
            "aie_partitions": {
                "partitions": [{
                    "hw_contexts": [
                        {
                            "context_id": "0",
                            "pid": "1234",
                            "instr_bo_mem": "2048 KB",
                            "command_submissions": 50,
                            "command_completions": 50,
                            "gops": 25.0,
                            "status": "Idle"
                        },
                        {
                            "context_id": "1", 
                            "pid": "5678",
                            "instr_bo_mem": "1024 KB",
                            "command_submissions": 25,
                            "command_completions": 25,
                            "gops": 12.5,
                            "status": "Running"
                        }
                    ]
                }]
            }
        }]
    }
    
    result = monitor.parse_xrt_json(json_data)
    
    assert result["device_count"] == 1
    assert result["instr_bo_kb"] == 3072  # 2048 + 1024
    assert result["command_submissions"] == 75  # 50 + 25
    assert result["command_completions"] == 75
    assert result["utilization_percent"] == 100.0
    assert result["gops"] == 37.5  # (25.0 + 12.5) / 2
    assert len(result["contexts"]) == 2


def test_npu_monitor_aggregate_metrics():
    """Test NPUMonitor.aggregate_metrics() with context data."""
    monitor = NPUMonitor()
    
    contexts = [
        {
            "context_id": "0",
            "pid": "1234", 
            "instr_bo_kb": 2048,
            "command_submissions": 50,
            "command_completions": 50,
            "gops": 25.0,
            "status": "Idle"
        },
        {
            "context_id": "1",
            "pid": "5678",
            "instr_bo_kb": 1024,
            "command_submissions": 25,
            "command_completions": 20,  # Not all completed
            "gops": 12.5,
            "status": "Running"
        }
    ]
    
    result = monitor.aggregate_metrics(contexts)
    
    assert result["device_count"] == 1
    assert result["instr_bo_kb"] == 3072
    assert result["command_submissions"] == 75
    assert result["command_completions"] == 70
    assert result["utilization_percent"] == 93.33  # 70/75 * 100
    assert result["gops"] == 18.75  # (25.0 + 12.5) / 2
    assert len(result["contexts"]) == 2


def test_npu_monitor_error_handling():
    """Test NPUMonitor error handling when xrt-smi fails."""
    monitor = NPUMonitor()
    
    with patch('subprocess.run') as mock_run:
        mock_proc = MagicMock()
        mock_proc.returncode = 1  # Command failed
        mock_run.return_value = mock_proc
        
        result = monitor.sample_npu()
        assert result == {}  # Should return empty dict on error