from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QTabWidget, QWidget, QPushButton, QListWidget, QLabel, QProgressBar

class MainWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestionnaire de mises à jour macOS")
        self.resize(800, 600)

        self.layout = QVBoxLayout()

        # Barre de statut
        self.status_label = QLabel("Statut : En attente")
        self.layout.addWidget(self.status_label)

        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)

        # Onglets
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        self.setup_updates_tab()
        self.setup_reports_tab()

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

    def setup_updates_tab(self):
        """
        Configure l'onglet des mises à jour
        """
        self.updates_tab = QWidget()
        layout = QVBoxLayout()

        self.check_updates_button = QPushButton("Vérifier les mises à jour Homebrew")
        layout.addWidget(self.check_updates_button)

        self.updates_list = QListWidget()
        layout.addWidget(self.updates_list)

        self.update_all_button = QPushButton("Mettre à jour tout")
        layout.addWidget(self.update_all_button)

        self.updates_tab.setLayout(layout)
        self.tab_widget.addTab(self.updates_tab, "Mises à jour")

    def setup_reports_tab(self):
        """
        Configure l'onglet des rapports
        """
        self.reports_tab = QWidget()
        layout = QVBoxLayout()

        self.export_button = QPushButton("Exporter le rapport")
        layout.addWidget(self.export_button)

        self.reports_tab.setLayout(layout)
        self.tab_widget.addTab(self.reports_tab, "Rapports")
