import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QListWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

PATIENTS = [
    {
        "name": "张三",
        "id": "P2024001",
        "gender": "男",
        "age": 45,
        "date": "2026-05-28",
        "diagnosis": "右肺上叶结节",
        "report": (
            "影像所见：\n"
            "右肺上叶可见一大小约 8mm×6mm 磨玻璃结节，边缘尚清，"
            "无分叶及毛刺征。双肺纹理清晰，肺门结构正常。纵隔未见肿大淋巴结。\n\n"
            "诊断意见：\n"
            "1. 右肺上叶磨玻璃结节（建议 3 个月复查）\n"
            "2. 双肺未见明显异常"
        ),
    },
    {
        "name": "李四",
        "id": "P2024002",
        "gender": "女",
        "age": 38,
        "date": "2026-05-27",
        "diagnosis": "左侧乳腺占位",
        "report": (
            "影像所见：\n"
            "左乳外上象限可见一大小约 15mm×12mm 低回声结节，边界清晰，"
            "形态规则，内部回声均匀。CDFI 示结节内部及周边可见少量血流信号。\n\n"
            "诊断意见：\n"
            "左乳外上象限实性结节（BI-RADS 3 级，建议短期复查）"
        ),
    },
    {
        "name": "王五",
        "id": "P2024003",
        "gender": "男",
        "age": 62,
        "date": "2026-05-26",
        "diagnosis": "腰椎间盘突出",
        "report": (
            "影像所见：\n"
            "腰椎生理曲度变直。L4/5、L5/S1 椎间盘向后突出，"
            "硬膜囊前缘受压。椎管未见明显狭窄。黄韧带未见肥厚。\n\n"
            "诊断意见：\n"
            "1. L4/5、L5/S1 椎间盘突出\n"
            "2. 腰椎退行性变"
        ),
    },
    {
        "name": "赵六",
        "id": "P2024004",
        "gender": "女",
        "age": 29,
        "date": "2026-05-25",
        "diagnosis": "正常体检",
        "report": (
            "影像所见：\n"
            "胸廓对称，双肺野清晰，肺纹理走形自然。心影大小形态正常。"
            "纵隔居中，未见明显异常密度影。双侧膈面光滑，肋膈角锐利。\n\n"
            "诊断意见：\n"
            "胸部 CT 平扫未见明显异常"
        ),
    },
]


class ReportDetailPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.info_frame = QFrame()
        self.info_frame.setFrameShape(QFrame.StyledPanel)
        info_layout = QGridLayout(self.info_frame)

        self.lb_name = QLabel()
        self.lb_id = QLabel()
        self.lb_gender = QLabel()
        self.lb_age = QLabel()
        self.lb_date = QLabel()
        self.lb_diagnosis = QLabel()

        font = QFont()
        font.setPointSize(12)
        for lb in [self.lb_name, self.lb_id, self.lb_gender, self.lb_age, self.lb_date, self.lb_diagnosis]:
            lb.setFont(font)

        info_layout.addWidget(QLabel("姓名："), 0, 0)
        info_layout.addWidget(self.lb_name, 0, 1)
        info_layout.addWidget(QLabel("病历号："), 0, 2)
        info_layout.addWidget(self.lb_id, 0, 3)
        info_layout.addWidget(QLabel("性别："), 1, 0)
        info_layout.addWidget(self.lb_gender, 1, 1)
        info_layout.addWidget(QLabel("年龄："), 1, 2)
        info_layout.addWidget(self.lb_age, 1, 3)
        info_layout.addWidget(QLabel("检查日期："), 2, 0)
        info_layout.addWidget(self.lb_date, 2, 1)
        info_layout.addWidget(QLabel("诊断："), 2, 2)
        info_layout.addWidget(self.lb_diagnosis, 2, 3)

        layout.addWidget(self.info_frame)

        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        report_font = QFont("Noto Sans CJK SC", 11)
        self.report_view.setFont(report_font)
        layout.addWidget(self.report_view)

    def show_report(self, patient):
        self.lb_name.setText(patient["name"])
        self.lb_id.setText(patient["id"])
        self.lb_gender.setText(patient["gender"])
        self.lb_age.setText(str(patient["age"]))
        self.lb_date.setText(patient["date"])
        self.lb_diagnosis.setText(patient["diagnosis"])
        self.report_view.setPlainText(patient["report"])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("影像报告系统")
        self.resize(900, 600)

        splitter = QSplitter(Qt.Horizontal)

        self.patient_list = QListWidget()
        self.patient_list.setMinimumWidth(200)
        self.patient_list.currentRowChanged.connect(self._on_select)

        for p in PATIENTS:
            self.patient_list.addItem(f"{p['name']} ({p['id']})")

        self.detail_panel = ReportDetailPanel()

        splitter.addWidget(self.patient_list)
        splitter.addWidget(self.detail_panel)
        splitter.setSizes([200, 700])

        self.setCentralWidget(splitter)

        if PATIENTS:
            self.patient_list.setCurrentRow(0)

    def _on_select(self, row):
        if 0 <= row < len(PATIENTS):
            self.detail_panel.show_report(PATIENTS[row])


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
