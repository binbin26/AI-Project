import json
import hashlib


PROJECT_SCHEMA_VERSION = 1


def compute_checksum(project_data: dict) -> str:
    data_copy = dict(project_data)
    if 'checksum' in data_copy:
        data_copy.pop('checksum')
    payload = json.dumps(data_copy, sort_keys=True, ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def attach_checksum(project_data: dict) -> dict:
    data = dict(project_data)
    data['version'] = PROJECT_SCHEMA_VERSION
    data['checksum'] = compute_checksum(data)
    return data


def validate_loaded_project(project_data: dict) -> None:
    if 'version' not in project_data:
        raise ValueError('Thiếu trường version trong dự án')
    if int(project_data['version']) != PROJECT_SCHEMA_VERSION:
        raise ValueError(f"Phiên bản dự án không hỗ trợ: {project_data['version']}")
    if 'checksum' not in project_data:
        raise ValueError('Thiếu checksum')
    checksum = project_data['checksum']
    expected = compute_checksum(project_data)
    if checksum != expected:
        raise ValueError('Checksum không khớp, tệp có thể bị sửa đổi')

