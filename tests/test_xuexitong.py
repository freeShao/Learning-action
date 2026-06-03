import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "xuexitong_script"))

from mainScript import (
    sanitize_filename,
    is_valid_url,
    clean_cache,
    download_picture,
    convert_images_to_pdf,
)


class TestSanitizeFilename:
    def test_normal_filename(self):
        assert sanitize_filename("hello") == "hello"

    def test_with_pdf_extension(self):
        assert sanitize_filename("test.pdf") == "test.pdf"

    def test_removes_path_traversal(self):
        result = sanitize_filename("../etc/passwd")
        assert ".." not in result.replace("_", "")
        assert "/" not in result

    def test_double_dot_becomes_underscore(self):
        assert sanitize_filename("..") == "_"

    def test_removes_special_chars(self):
        result = sanitize_filename("a<b>c:d|e?f*g")
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert "|" not in result

    def test_handles_empty_string(self):
        assert sanitize_filename("") == "output"

    def test_handles_whitespace_only(self):
        assert sanitize_filename("   ") == "output"

    def test_preserves_chinese(self):
        result = sanitize_filename("你好世界")
        assert "你好世界" in result

    def test_preserves_hyphen_and_dot(self):
        result = sanitize_filename("my-file_v2.0")
        assert result == "my-file_v2.0"


class TestIsValidUrl:
    def test_https_url(self):
        assert is_valid_url("https://example.com/thumb/") is True

    def test_http_url(self):
        assert is_valid_url("http://example.com/test") is True

    def test_file_protocol_rejected(self):
        assert is_valid_url("file:///etc/passwd") is False

    def test_javascript_rejected(self):
        assert is_valid_url("javascript:alert(1)") is False

    def test_empty_string_rejected(self):
        assert is_valid_url("") is False

    def test_plain_text_rejected(self):
        assert is_valid_url("not a url") is False


class TestCleanCache:
    def test_clean_png_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                with open(os.path.join(tmpdir, f"{i}.png"), "w") as f:
                    f.write("test")
            with open(os.path.join(tmpdir, "notes.txt"), "w") as f:
                f.write("test")

            deleted = clean_cache(tmpdir, "*.png")
            assert deleted == 3

            remaining = os.listdir(tmpdir)
            assert remaining == ["notes.txt"]

    def test_clean_no_match(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test.txt"), "w") as f:
                f.write("test")
            deleted = clean_cache(tmpdir, "*.png")
            assert deleted == 0

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            deleted = clean_cache(tmpdir, "*.*")
            assert deleted == 0

    def test_non_existent_directory(self):
        deleted = clean_cache("/nonexistent/path", "*.*")
        assert deleted == 0

    def test_path_traversal_protection(self):
        """clean_cache should not delete files outside the target directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            outer_file = os.path.join(tempfile.gettempdir(), "should_not_exist.txt")
            if os.path.exists(outer_file):
                os.remove(outer_file)

            deleted = clean_cache(tmpdir, "*.txt")
            assert deleted == 0
