import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from main import PATIENTS, MainWindow, ReportDetailPanel


@pytest.fixture(scope="function")
def qtapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def window(qtapp):
    w = MainWindow()
    w.show()
    yield w
    w.close()


class TestPatientData:
    def test_patient_count(self):
        assert len(PATIENTS) == 4

    @pytest.mark.parametrize("key", ["name", "id", "gender", "age", "date", "diagnosis", "report"])
    def test_patient_has_all_fields(self, key):
        for p in PATIENTS:
            assert key in p, f"{p['name']} missing '{key}'"

    def test_all_ids_unique(self):
        ids = [p["id"] for p in PATIENTS]
        assert len(ids) == len(set(ids))

    def test_all_reports_not_empty(self):
        for p in PATIENTS:
            assert len(p["report"]) > 50


class TestReportDetailPanel:
    def test_show_report_updates_labels(self, qtapp):
        panel = ReportDetailPanel()
        patient = PATIENTS[0]
        panel.show_report(patient)
        assert panel.lb_name.text() == patient["name"]
        assert panel.lb_id.text() == patient["id"]
        assert panel.lb_gender.text() == patient["gender"]
        assert panel.lb_age.text() == str(patient["age"])
        assert panel.lb_date.text() == patient["date"]
        assert panel.lb_diagnosis.text() == patient["diagnosis"]
        assert panel.report_view.toPlainText() == patient["report"]
        panel.deleteLater()

    def test_switch_patient_updates_all_fields(self, qtapp):
        panel = ReportDetailPanel()
        panel.show_report(PATIENTS[0])
        panel.show_report(PATIENTS[1])
        assert panel.lb_name.text() == PATIENTS[1]["name"]
        assert panel.lb_id.text() == PATIENTS[1]["id"]
        panel.deleteLater()

    def test_survives_empty_data(self, qtapp):
        panel = ReportDetailPanel()
        panel.show_report({
            "name": "", "id": "", "gender": "",
            "age": 0, "date": "", "diagnosis": "",
            "report": ""
        })
        assert panel.lb_name.text() == ""
        assert panel.report_view.toPlainText() == ""
        panel.deleteLater()

    def test_long_report_text(self, qtapp):
        panel = ReportDetailPanel()
        long_report = "a" * 10000
        panel.show_report({**PATIENTS[0], "report": long_report})
        assert len(panel.report_view.toPlainText()) == 10000
        panel.deleteLater()


class TestMainWindow:
    def test_window_title(self, window):
        assert window.windowTitle() == "影像报告系统"

    def test_patient_list_count(self, window):
        assert window.patient_list.count() == len(PATIENTS)

    def test_initial_selection_shows_first_patient(self, window):
        assert window.patient_list.currentRow() == 0
        first = PATIENTS[0]
        assert window.detail_panel.lb_name.text() == first["name"]

    def test_clicking_patient_updates_detail(self, window):
        window.patient_list.setCurrentRow(1)
        assert window.detail_panel.lb_name.text() == PATIENTS[1]["name"]

    @pytest.mark.parametrize("index", range(len(PATIENTS)))
    def test_each_patient_shows_correctly(self, window, index):
        window.patient_list.setCurrentRow(index)
        p = PATIENTS[index]
        assert window.detail_panel.lb_name.text() == p["name"]
        assert window.detail_panel.lb_id.text() == p["id"]
        assert window.detail_panel.report_view.toPlainText() == p["report"]
