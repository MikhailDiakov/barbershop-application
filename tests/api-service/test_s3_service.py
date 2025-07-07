from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException

from app.services.s3_service import delete_file_from_s3, upload_file_to_s3


@pytest.mark.asyncio
@patch("app.services.s3_service.s3_client.put_object")
async def test_upload_file_success(mock_put_object):
    mock_put_object.return_value = {}

    url = await upload_file_to_s3(b"test bytes", "test.txt", "text/plain")
    assert "barbers/" in url
    assert url.endswith("test.txt")


@pytest.mark.asyncio
@patch("app.services.s3_service.s3_client.put_object")
async def test_upload_file_failure(mock_put_object):
    mock_put_object.side_effect = ClientError({"Error": {}}, "PutObject")

    with pytest.raises(HTTPException) as exc_info:
        await upload_file_to_s3(b"test bytes", "test.txt", "text/plain")
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
@patch("app.services.s3_service.s3_client.delete_object")
async def test_delete_file_success(mock_delete_object):
    mock_delete_object.return_value = {}

    await delete_file_from_s3("some/key")


@pytest.mark.asyncio
@patch("app.services.s3_service.s3_client.delete_object")
async def test_delete_file_failure(mock_delete_object):
    mock_delete_object.side_effect = ClientError({"Error": {}}, "DeleteObject")

    with pytest.raises(HTTPException) as exc_info:
        await delete_file_from_s3("some/key")
    assert exc_info.value.status_code == 500
