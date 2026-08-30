import pytest

from app.services.upload import (
    LocalFileUploadConfig,
    LocalFileUploader,
    build_public_id,
)


class TestLocalFileUploadConfig:
    def test_default_storage_path(self):
        config = LocalFileUploadConfig()
        assert config.storage_path == config.storage_path  # Path object
        # Docker path format (forward slashes even on Windows)
        assert str(config.storage_path).replace("\\", "/") == "/app/uploads"

    def test_custom_storage_dir(self, tmp_path):
        config = LocalFileUploadConfig(storage_dir=str(tmp_path))
        assert config.storage_path == tmp_path

    def test_custom_url_prefix(self):
        config = LocalFileUploadConfig(url_prefix="/media/images")
        assert config.url_prefix == "/media/images"


class TestLocalFileUploader:
    def test_upload_image_stores_file_and_returns_url(self, tmp_path):
        config = LocalFileUploadConfig(storage_dir=str(tmp_path), url_prefix="/uploads")
        uploader = LocalFileUploader(config)

        source = tmp_path / "source.png"
        source.write_bytes(b"fake-image-data")

        result = uploader.upload_image(
            file_path=str(source),
            filename="test.png",
            user_id=42,
        )

        assert result is not None
        assert result.url.startswith("/uploads/")
        assert "pickups/42/" in result.url
        assert ".png" in result.url
        assert "test.png" not in result.url
        assert result.public_id.startswith("pickups/42/")
        assert result.public_id.endswith(".png")

    def test_upload_image_without_user_id(self, tmp_path):
        config = LocalFileUploadConfig(storage_dir=str(tmp_path))
        uploader = LocalFileUploader(config)

        source = tmp_path / "source.jpg"
        source.write_bytes(b"fake-jpg-data")

        result = uploader.upload_image(
            file_path=str(source),
            filename="anon.jpg",
            user_id=None,
        )

        assert result is not None
        assert result.url.startswith("/uploads/")
        assert result.public_id.startswith("pickups/")
        # public_id format matches build_public_id: pickups/{uuid}.{ext}
        # (no user folder when user_id=None)
        parts = result.public_id.split("/")
        assert len(parts) == 2
        assert parts[0] == "pickups"

    def test_upload_image_removes_source_file(self, tmp_path):
        config = LocalFileUploadConfig(storage_dir=str(tmp_path))
        uploader = LocalFileUploader(config)

        source = tmp_path / "temp.png"
        source.write_bytes(b"data")

        uploader.upload_image(file_path=str(source), filename="temp.png", user_id=1)

        assert not source.exists()

    def test_upload_image_moves_file_to_per_user_folder(self, tmp_path):
        config = LocalFileUploadConfig(storage_dir=str(tmp_path))
        uploader = LocalFileUploader(config)

        source = tmp_path / "source.webp"
        source.write_bytes(b"webp-bytes")

        uploader.upload_image(file_path=str(source), filename="test.webp", user_id=7)

        namespace_dir = tmp_path / "pickups" / "7"
        stored_files = list(namespace_dir.glob("*"))
        assert len(stored_files) == 1
        assert stored_files[0].name.endswith(".webp")

    def test_upload_image_unknown_extension_uses_path_suffix(self, tmp_path):
        config = LocalFileUploadConfig(storage_dir=str(tmp_path))
        uploader = LocalFileUploader(config)

        source = tmp_path / "noextension"
        source.write_bytes(b"bytes")

        result = uploader.upload_image(file_path=str(source), filename="noextension", user_id=1)

        assert result is not None
        # UUID is appended even without extension
        assert result.public_id.startswith("pickups/1/")

    def test_upload_image_raises_when_source_missing(self, tmp_path):
        from app.services.upload import ImageUploadUnavailableError

        config = LocalFileUploadConfig(storage_dir=str(tmp_path))
        uploader = LocalFileUploader(config)

        with pytest.raises(ImageUploadUnavailableError):
            uploader.upload_image(
                file_path=str(tmp_path / "does-not-exist.png"),
                filename="missing.png",
                user_id=1,
            )

    def test_delete_image_removes_stored_file(self, tmp_path):
        config = LocalFileUploadConfig(storage_dir=str(tmp_path))
        uploader = LocalFileUploader(config)

        # Create a file to delete
        target = tmp_path / "pickups" / "1" / "abc123.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"stored-image")

        result = uploader.delete_image(public_id="pickups/1/abc123.png")

        assert result is True
        assert not target.exists()

    def test_delete_image_idempotent_for_missing_file(self, tmp_path):
        config = LocalFileUploadConfig(storage_dir=str(tmp_path))
        uploader = LocalFileUploader(config)

        result = uploader.delete_image(public_id="pickups/1/does-not-exist.png")

        assert result is True  # Missing asset counts as successfully deleted

    def test_delete_image_raises_on_os_error(self, tmp_path):
        from app.services.upload import ImageDeleteError

        config = LocalFileUploadConfig(storage_dir=str(tmp_path))
        uploader = LocalFileUploader(config)

        # Create a read-only file to simulate deletion failure
        target = tmp_path / "pickups" / "1" / "readonly.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"data")
        target.chmod(0o444)  # Read-only

        try:
            with pytest.raises(ImageDeleteError):
                uploader.delete_image(public_id="pickups/1/readonly.png")
        finally:
            # Restore permissions so cleanup can happen
            target.chmod(0o644)


class TestBuildPublicId:
    def test_format_is_consistent_across_providers(self):
        # The public_id format must be consistent between Cloudinary and local
        # storage so that database references are interchangeable.
        pid = build_public_id(user_id=99, filename="waste.jpg")
        assert pid.startswith("pickups/99/")
        suffix = pid.split("/")[-1]
        assert len(suffix) == 32
        assert all(c in "0123456789abcdef" for c in suffix)
        assert ".jpg" not in pid  # extension is not embedded in public_id
