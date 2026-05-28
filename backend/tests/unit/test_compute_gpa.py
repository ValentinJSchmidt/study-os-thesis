"""Tests for the pure _compute_gpa function from app.students.service."""

import pytest

from app.students.schemas import StudentCourseItem
from app.students.service import _compute_gpa


def _course(name: str, credits: float | None, grade: str | None) -> StudentCourseItem:
    return StudentCourseItem(course_name=name, credits=credits, grade=grade)


@pytest.mark.unit
class TestComputeGpa:
    def test_gpa_three_courses(self):
        courses = [
            _course("A", 5.0, "1,3"),
            _course("B", 5.0, "2,0"),
            _course("C", 5.0, "3,0"),
        ]
        result = _compute_gpa(courses)
        expected = round((1.3 * 5 + 2.0 * 5 + 3.0 * 5) / 15, 2)
        assert result == expected

    def test_gpa_weighted_by_credits(self):
        courses = [
            _course("Easy", 1.0, "1,0"),
            _course("Hard", 5.0, "3,0"),
        ]
        result = _compute_gpa(courses)
        expected = round((1.0 * 1 + 3.0 * 5) / 6, 2)
        assert result == expected

    def test_gpa_empty_list(self):
        assert _compute_gpa([]) is None

    def test_gpa_all_invalid_grades(self):
        courses = [
            _course("A", 5.0, "bestanden"),
            _course("B", 3.0, "passed"),
        ]
        assert _compute_gpa(courses) is None

    def test_gpa_mixed_valid_and_invalid(self):
        courses = [
            _course("A", 5.0, "1,3"),
            _course("B", 3.0, "bestanden"),
            _course("C", 4.0, "2,7"),
        ]
        result = _compute_gpa(courses)
        expected = round((1.3 * 5 + 2.7 * 4) / 9, 2)
        assert result == expected

    def test_gpa_german_comma_format(self):
        courses = [_course("A", 5.0, "1,3")]
        result = _compute_gpa(courses)
        assert result == 1.3

    def test_gpa_rounds_to_two_decimals(self):
        courses = [
            _course("A", 3.0, "1,3"),
            _course("B", 7.0, "2,7"),
        ]
        result = _compute_gpa(courses)
        assert result is not None
        assert result == round(result, 2)

    def test_gpa_none_credits_skipped(self):
        courses = [
            _course("A", None, "1,3"),
            _course("B", 5.0, "2,0"),
        ]
        result = _compute_gpa(courses)
        assert result == 2.0

    def test_gpa_none_grade_skipped(self):
        courses = [
            _course("A", 5.0, None),
            _course("B", 5.0, "2,0"),
        ]
        result = _compute_gpa(courses)
        assert result == 2.0

    def test_gpa_grade_outside_range_skipped(self):
        courses = [
            _course("A", 5.0, "0,5"),  # below 1.0
            _course("B", 5.0, "5,5"),  # above 5.0
            _course("C", 5.0, "2,0"),
        ]
        result = _compute_gpa(courses)
        assert result == 2.0
