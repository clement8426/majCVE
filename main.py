import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QCheckBox, QMessageBox,
    QHeaderView, QProgressBar, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from modules.updater import list_homebrew_upgrades, update_package
from modules.cve_check import analyze_cve
from modules.logger_utils import setup_logger
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

logger = setup_logger()


class FetchUpdatesThread(QThread):
    """
    Thread pour rechercher les mises à jour disponibles via Homebrew.
    """
    updates_fetched = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            updates = list_homebrew_upgrades()
            self.updates_fetched.emit(updates)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestionnaire de mises à jour")
        self.resize(1000, 600)

        # Variables
        self.updates = []

        # Layout principal
        self.main_layout = QVBoxLayout()

        # Label de statut
        self.status_label = QLabel("Statut : En attente d'une action utilisateur")
        self.status_label.setAlignment(Qt.AlignLeft)
        self.main_layout.addWidget(self.status_label)

        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)

        # Tableau des mises à jour
        self.updates_table = QTableWidget(0, 6)
        self.updates_table.setHorizontalHeaderLabels([
            "Nom", "Version actuelle", "Nouvelle version", "CVE", "CVSS", "Sélectionner"
        ])
        self.updates_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.main_layout.addWidget(self.updates_table)

        # Boutons
        self.button_layout = QHBoxLayout()
        self.check_updates_button = QPushButton("Rechercher les mises à jour")
        self.check_updates_button.clicked.connect(self.start_fetch_updates)
        self.button_layout.addWidget(self.check_updates_button)

        self.update_selected_button = QPushButton("Mettre à jour les éléments sélectionnés")
        self.update_selected_button.clicked.connect(self.update_selected_items)
        self.update_selected_button.setEnabled(False)
        self.button_layout.addWidget(self.update_selected_button)

        self.update_all_button = QPushButton("Mettre à jour tout")
        self.update_all_button.clicked.connect(self.update_all_items)
        self.update_all_button.setEnabled(False)
        self.button_layout.addWidget(self.update_all_button)

        self.generate_pdf_button = QPushButton("Générer le PDF")
        self.generate_pdf_button.setEnabled(False)
        self.generate_pdf_button.clicked.connect(self.generate_report_pdf)
        self.button_layout.addWidget(self.generate_pdf_button)

        self.main_layout.addLayout(self.button_layout)

        # Conteneur principal
        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

        # Thread
        self.fetch_thread = None

    def start_fetch_updates(self):
        """
        Démarre la recherche des mises à jour.
        """
        self.status_label.setText("Recherche des mises à jour en cours...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.check_updates_button.setEnabled(False)
        self.update_selected_button.setEnabled(False)
        self.update_all_button.setEnabled(False)
        self.generate_pdf_button.setEnabled(False)

        self.fetch_thread = FetchUpdatesThread()
        self.fetch_thread.updates_fetched.connect(self.display_updates)
        self.fetch_thread.error_occurred.connect(self.handle_fetch_error)
        self.fetch_thread.start()

    def display_updates(self, updates):
        """
        Affiche les mises à jour disponibles avec les informations CVE et CVSS.
        """
        self.progress_bar.setVisible(False)
        self.updates_table.setRowCount(0)
        self.updates = updates

        if not updates:
            self.status_label.setText("Aucune mise à jour disponible.")
            QMessageBox.information(self, "Info", "Aucune mise à jour trouvée.")
            self.check_updates_button.setEnabled(True)
            return

        self.status_label.setText(f"{len(updates)} mise(s) à jour trouvée(s).")
        for update in updates:
            row_position = self.updates_table.rowCount()
            self.updates_table.insertRow(row_position)

            # Informations sur le package
            name_item = QTableWidgetItem(update["name"])
            current_version_item = QTableWidgetItem(update["current_version"])
            new_version_item = QTableWidgetItem(update["new_version"])

            # Analyse CVE
            try:
                security, cve_current, cve_new = analyze_cve(
                    update["current_version"],
                    update["new_version"],
                    vendor="apple",
                    product=update["name"]
                )
                cve_list = ", ".join([cve["id"] for cve in cve_new]) if cve_new else "N/A"
                cvss_scores = ", ".join([str(cve.get("score", "N/A")) for cve in cve_new]) if cve_new else "N/A"
            except Exception as e:
                logger.error(f"Erreur d'analyse CVE pour {update['name']}: {e}")
                cve_list = "N/A"
                cvss_scores = "N/A"

            cve_item = QTableWidgetItem(cve_list)
            cvss_item = QTableWidgetItem(cvss_scores)

            # Case à cocher pour la sélection
            checkbox = QCheckBox()
            checkbox.setToolTip(f"Sélectionner pour mettre à jour {update['name']}")
            self.updates_table.setCellWidget(row_position, 5, checkbox)

            # Remplir les colonnes
            self.updates_table.setItem(row_position, 0, name_item)
            self.updates_table.setItem(row_position, 1, current_version_item)
            self.updates_table.setItem(row_position, 2, new_version_item)
            self.updates_table.setItem(row_position, 3, cve_item)
            self.updates_table.setItem(row_position, 4, cvss_item)

        self.update_selected_button.setEnabled(True)
        self.update_all_button.setEnabled(True)
        self.generate_pdf_button.setEnabled(True)
        self.check_updates_button.setEnabled(True)

    def handle_fetch_error(self, error_message):
        """
        Gère les erreurs lors de la recherche de mises à jour.
        """
        self.progress_bar.setVisible(False)
        self.status_label.setText("Erreur lors de la recherche des mises à jour.")
        QMessageBox.critical(self, "Erreur", error_message)
        self.check_updates_button.setEnabled(True)

    def update_selected_items(self):
        """
        Met à jour uniquement les éléments sélectionnés.
        """
        selected_rows = [
            row for row in range(self.updates_table.rowCount())
            if self.updates_table.cellWidget(row, 5).isChecked()
        ]

        if not selected_rows:
            QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner au moins un élément.")
            return

        for row in selected_rows:
            package_name = self.updates_table.item(row, 0).text()
            self.status_label.setText(f"Mise à jour de {package_name} en cours...")
            success, message = update_package(package_name)
            if success:
                QMessageBox.information(self, "Succès", f"{package_name} mis à jour avec succès.")
            else:
                QMessageBox.warning(self, "Erreur", f"Erreur lors de la mise à jour de {package_name} : {message}")

        self.status_label.setText("Mises à jour terminées.")

    def update_all_items(self):
        """
        Met à jour tous les éléments affichés.
        """
        for update in self.updates:
            package_name = update["name"]
            self.status_label.setText(f"Mise à jour de {package_name} en cours...")
            success, message = update_package(package_name)
            if success:
                logger.info(f"{package_name} mis à jour avec succès.")
            else:
                logger.error(f"Erreur lors de la mise à jour de {package_name} : {message}")

        self.status_label.setText("Toutes les mises à jour ont été terminées.")
        QMessageBox.information(self, "Info", "Toutes les mises à jour ont été effectuées.")

    def generate_report_pdf(self):
        """
        Génère un fichier PDF contenant le compte rendu des mises à jour.
        """
        file_path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder le rapport PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return

        try:
            pdf = canvas.Canvas(file_path, pagesize=A4)
            pdf.setFont("Helvetica", 10)
            pdf.drawString(50, 800, "Rapport des mises à jour")
            pdf.drawString(50, 780, "Généré par le Gestionnaire de mises à jour")

            y = 760
            for row in range(self.updates_table.rowCount()):
                name = self.updates_table.item(row, 0).text()
                current_version = self.updates_table.item(row, 1).text()
                new_version = self.updates_table.item(row, 2).text()
                cve = self.updates_table.item(row, 3).text()
                cvss = self.updates_table.item(row, 4).text()

                pdf.drawString(50, y, f"Nom: {name}")
                pdf.drawString(150, y, f"Version actuelle: {current_version}")
                pdf.drawString(350, y, f"Nouvelle version: {new_version}")
                pdf.drawString(550, y, f"CVE: {cve}")
                pdf.drawString(700, y, f"CVSS: {cvss}")
                y -= 20

                if y < 50:  # Crée une nouvelle page si nécessaire
                    pdf.showPage()
                    pdf.setFont("Helvetica", 10)
                    y = 800

            pdf.save()
            QMessageBox.information(self, "Succès", "Rapport PDF généré avec succès.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de générer le PDF : {e}")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
