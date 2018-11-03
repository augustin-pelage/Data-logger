"""Data_logger.py, stage 2018 Augustin Pelage"""

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog, QFileDialog, QPushButton, QLabel, QSpinBox, QWidget, QTreeWidget, QTreeWidgetItem, QAction
from PyQt5.uic import loadUiType
from PyQt5 import QtCore
from vna_2_2_1 import VNA
import warnings
import sys
import time
import pyqtgraph as pg
import pickle
import os
import numpy as np

from datetime import datetime
from UImainwindow import *
from UIImpedance import *
from os.path import basename
import shutil
#from functools import partial

#Classe principale du data logger
class Data_logger(QtWidgets.QMainWindow):

    #Initialisation de la classe
    def __init__(self, parent=None):
        super(Data_logger, self).__init__(parent=parent)

        #Chargement et affichage de la classe de l'interface graphique du data logger
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

            #Connexion signaux slots
        self.timer = QtCore.QTimer()
        self.timer_calib = QtCore.QTimer()
        self.timer_pause = QtCore.QTimer()
        self.ui.pushButton_8.clicked.connect(self.stop_data_logger)
        self.timer.timeout.connect(self.is_data_ready)
        self.timer_calib.timeout.connect(self.is_data_single_ready)
        self.timer_pause.timeout.connect(self.verif_pause)

        self.ui.toolButton.clicked.connect(self.connection)

        self.ui.file_select_button_3.clicked.connect(self.select_file_configuration)
        self.ui.file_select_button_4.clicked.connect(self.select_file_acquisition)

        self.ui.pushButton_5.clicked.connect(self.edit_measure)

        self.ui.pushButton_2.clicked.connect(self.add_acquisition)
        self.ui.pushButton_4.clicked.connect(self.add_measure)
        self.ui.doubleSpinBox_6.valueChanged.connect(self.actualise_param_acquisition)
        self.ui.doubleSpinBox_7.valueChanged.connect(self.actualise_param_acquisition)
        self.ui.doubleSpinBox_8.valueChanged.connect(self.actualise_param_acquisition)

        self.ui.comboBox_4.currentIndexChanged.connect(self.actualise_data_plot_list)

        self.ui.pushButton_3.clicked.connect(self.remove_item)
        self.ui.pushButton_7.clicked.connect(self.call_data_logger)
        self.ui.pushButton_9.clicked.connect(self.pause_acquisition)
        self.ui.treeWidget.itemSelectionChanged.connect(self.param_select_acquisition)

        #self.ui.treeWidget.itemClicked[QTreeWidgetItem, int].connect(self.select_acquisition)
        #self.ui.treeWidget.itemSelectionChanged.connect(self.param_select_acquisition)
        self.is_acquisition_active = False #Pas d'acquisition en cours

        self.p1 = None
        self.p2 = None

        self.ui.pushButton_8.setEnabled(False)
        self.compteur_acquistion = 0
        self.value = 0
        self.sauv_value = 0
        self.donnees = [] #Aucune donné n'est lue
        self.connection = False
        self.freq_open = None
        self.freq_short = None
        self.freq_load = None
        self.open_data = None
        self.short_data = None
        self.load_data = None
        self.is_impedance_alrealy_init = False
        self.ensemble_meas_z_module_max_evolution = []
        self.is_pause = False

        self.ui.pushButton_5.setEnabled(False)
        self.ui.pushButton_4.setEnabled(False)
        self.ui.doubleSpinBox_6.setEnabled(False)
        self.ui.doubleSpinBox_7.setEnabled(False)
        self.ui.doubleSpinBox_8.setEnabled(False)
        self.ui.pushButton_9.setEnabled(False)
        self.ui.pushButton_3.setEnabled(False)
        self.ui.pushButton_7.setEnabled(False)


        self.select_item = ""


        self.acquisition_list = []
        self.ensemble_item_acquisition = []
        self.ensemble_item = []
        self.actualise_acquisition_list()

        if os.path.exists('config') == False: #Si le fichier de configuration n'existe pas.
            with open("config", 'wb') as file_:
                pickle.dump(os.getcwd() + "\Configuration", file_)
                pickle.dump(os.getcwd() + "\Data", file_)

#On essai de récupérer les anciens chemins de stockage (sauvegarde) des config et des acquisitions

        with open("config", 'rb') as file_:
            path_config = pickle.load(file_)
            path_acquisition = pickle.load(file_)

        if os.path.exists(path_config):
            self.ui.lineEdit_6.setText(path_config)
        else:
            try:
                self.ui.lineEdit_6.setText(os.getcwd() + "\Configuration")
                os.mkdir(os.getcwd() + "\Configuration")
            except OSError:
                pass

        if os.path.exists(path_acquisition):
            self.ui.lineEdit_5.setText(path_acquisition)
        else:
            try:
                self.ui.lineEdit_5.setText(os.getcwd() + "\Data")
                os.mkdir(os.getcwd() + "\Data")
            except OSError:
                pass

        self.load_list_acquisition()

#################Gestion du module d'analyse vectorielle d'impédance de Pavel#############
    def init_impedance(self):
        windows_Impedance.ui.pushButton_21.clicked.connect(self.open) #open
        windows_Impedance.ui.pushButton_19.clicked.connect(self.short) #short
        windows_Impedance.ui.pushButton_20.clicked.connect(self.load) #load
        #windows_Impedance.ui.pushButton_22.clicked.connect(self.single) #single
        windows_Impedance.ui.pushButton_23.clicked.connect(self.close_impedance)
        windows_Impedance.ui.pushButton_22.clicked.connect(self.single_calib)
        self.is_impedance_alrealy_init = True

    def single_calib(self):
        self.charge_parametre_osl()
        window_VNA.sweep('dut')
        self.timer_calib.start(1)

    def is_data_single_ready(self):
        if window_VNA.reading == False:
            self.read_data_single() #Lecture des données de la dernière mesure effectuée
            self.process_data_single()
            #self.view_and_save_data(x, y, z)
            x1 = self.meas_frequ
            y1 = self.meas_z_module
            x2 = x1
            y2 = self.meas_z_arg
            label_x = "Time"
            label_y1 = "|z|"
            label_y2 = "Arg"

            self.plot_data_osl(x1, y1, x2, y2, label_x, label_y1, label_y2)


    def affiche_impedance(self):
        if self.is_impedance_alrealy_init == False:
            self.init_impedance()
        windows_Impedance.show()
        if self.connection == False:
            windows_Impedance.ui.pushButton_19.setEnabled(False)
            windows_Impedance.ui.pushButton_20.setEnabled(False)
            windows_Impedance.ui.pushButton_21.setEnabled(False)

    def close_impedance(self):
        self.sauv_param_impedance(self.ui.lineEdit_6.text() + "/" + self.current_acquisition.text(0) + "/" + self.current_general_item.text(0) + ".msr")
        windows_Impedance.hide()

    def sauv_param_impedance(self, path):
        with open(path, 'wb') as measure_file:
            pickle.dump("Impédance", measure_file)
            pickle.dump(windows_Impedance.ui.spinBox_3.value(), measure_file)
            pickle.dump(windows_Impedance.ui.comboBox_2.currentIndex(), measure_file)
            pickle.dump(windows_Impedance.ui.spinBox.value(), measure_file)
            pickle.dump(windows_Impedance.ui.spinBox_2.value(), measure_file)
            pickle.dump(windows_Impedance.ui.spinBox_15.value(), measure_file)
            pickle.dump(windows_Impedance.ui.spinBox_13.value(), measure_file)
            pickle.dump(windows_Impedance.ui.spinBox_14.value(), measure_file)
            pickle.dump(windows_Impedance.ui.spinBox_16.value(), measure_file)
            pickle.dump(windows_Impedance.ui.spinBox_4.value(), measure_file)
            pickle.dump(self.open_data, measure_file)
            pickle.dump(self.short_data, measure_file)
            pickle.dump(self.load_data, measure_file)
##########################################################################################

    #Récupère les paramètres de l'IHM et lance le data logger
    def call_data_logger(self):
        self.current_acquisition = self.ui.treeWidget.findItems(self.ui.comboBox.currentText(), QtCore.Qt.MatchRecursive)[0]
        #print("self.current_acquisition= ", self.current_acquisition)
        self.charge_acquistion(self.ui.comboBox.currentText())
        self.tps_between_two = self.ui.doubleSpinBox_6.value()
        self.nb_acquisition = self.ui.doubleSpinBox_7.value()
        self.max_duration = self.ui.doubleSpinBox_8.value()
        self.meas_z_module_max_value_evolution = []
        self.meas_z_module_max_freq_evolution = []
        self.meas_z_module_max_time_evolution = []
        self.meas_z_arg_max_value_evolution = []
        self.meas_z_arg_max_freq_evolution = []
        self.meas_z_arg_max_time_evolution = []
        self.save_meas_max_evolution = []
        self.parametre_list = []
        for acquisition in self.acquisition_list:
            if acquisition == self.ui.comboBox.currentText():
                for measure_list in self.list_item_measure_acqu[self.acquisition_list.index(acquisition)]:
                    for measure in measure_list:
                        with open(self.ui.lineEdit_6.text() + "/" + measure.parent().text(0) + "/" + measure.text(0) + ".msr", 'rb') as file_:
                            instrument = pickle.load(file_)
                            if instrument == "Impédance":
                                nb_point = pickle.load(file_)
                                bandwidth = pickle.load(file_)
                                start = pickle.load(file_)
                                stop = pickle.load(file_)
                                phase2 = pickle.load(file_)
                                phase1 = pickle.load(file_)
                                level1 = pickle.load(file_)
                                level2 = pickle.load(file_)
                                freq_corr = pickle.load(file_)
                                z_open = pickle.load(file_)
                                z_short = pickle.load(file_)
                                z_load = pickle.load(file_)
                            self.parametre_list.append([instrument, nb_point, bandwidth, start, stop, phase2, phase1, level1, level2, freq_corr, z_open, z_short, z_load])

        self.instrument_list = []
        for list_parametre_mesure in self.parametre_list:
            self.instrument_list.append(list_parametre_mesure[0])
        """self.parametre_list --> liste des listes de paramètres de chaque configuration
            self.instrument_list --> Liste de instruments utilisé durant l'acquisition"""

        self.ui.pushButton_8.setEnabled(True) #Activation du boutton Stop
        self.ui.pushButton_9.setEnabled(True) #Activation du boutton Pause
        self.compteur_acquistion = 0 #On remet le numéro d'acquisition courante à 0
        self.nb_measure = len(self.instrument_list) #Nombre de mesure à effectuer avant de passer à l'acquisition suivante
        self.compteur_measure = 0 #On remet le numéro de mesure courante à 0
        self.is_acquisition_active = True #Une acquisition est en cours

        list_empty_measure_evolution = []
        for measure in range(0, int(self.nb_measure)):
            list_empty_measure_evolution.append([])
        self.meas_z_max_evolution = list_empty_measure_evolution
        for measure in range(0, len(self.meas_z_max_evolution)):
            self.meas_z_max_evolution[measure] = [[], [], [], [], [], []]

        self.start_data_logger()

    #Lancement du data logger
    def start_data_logger(self):
        is_vna_pavel = False
        for instrument in self.instrument_list:
            if instrument == "Impédance":
                is_vna_pavel = True
        print("start data_logger")
        if is_vna_pavel == True:
            window_VNA.progressBar.valueChanged[int].connect(self.progress_bar) #Connexion de la barre de chargement avec celle du programme de Pavel

        if self.max_duration > 0: #Si un temps max est configuré
            self.timer.singleShot(self.max_duration * 1000, self.stop_data_logger) #On programme l'arret du data logger dans max_duration (ms)
        self.start_total_time_compteur = time.time() #Enregistrement du moment ou commence l'acquisition

        self.set_parameters()
        self.measure() #Lance une première mesure

    #effectue une nouvelle mesure (exemple: balayage en fréquence pour analyse d'impédance)
    def measure(self):
        if self.compteur_acquistion == self.nb_acquisition:
            self.ui.label_8.setText("Acquisition " + str(self.compteur_acquistion + 1))
        if self.compteur_acquistion == self.ui.doubleSpinBox_7.value(): #Si on a atteint le nombre d'acquisition programmé
            self.stop_data_logger() #On stop le data logger
        if self.is_acquisition_active == True: #Si le data logger est bien en cours de fonctionnement
            print("Do single step")
            self.start_time_compteur = time.time() #Enregistrement du moment ou commence la mesure
            self.sweep()

    #On Vérifie que la dernière mesure est bien terminé et on relance measure()
    def is_data_ready(self):
        if self.instrument_list[self.compteur_measure] == "Impédance":
            if window_VNA.reading == False: #Si la mesure est terminée
                self.next_measure()
        """if self.interface == "PyRpl":
            if mesure_finie: #Si la mesure est terminée
                self.next_measure()"""

    def next_measure(self):
        self.stop_time_compteur = time.time() #Enregistrement du moment ou fini la mesure
        self.compteur_measure += 1
        if self.compteur_measure == self.nb_measure:
            self.compteur_acquistion += 1
            self.compteur_measure = 0
        self.sauv_value = 0 #Barre de chargement à 0
        self.timer.stop() #On arret la vérification de la fin d'une mesure
        self.read_data() #Lecture des données de la dernière mesure effectuée
        self.process_data(self.freq, self.z)
        #self.view_and_save_data(x, y, z)
        self.update_max_evolution_list()
        self.view_and_save_data()
        self.timer_pause.start(1) #Vérification d'une éventuelle pause

    def verif_pause(self):
        if self.is_pause == False:
            self.timer_pause.stop()
            self.set_parameters()
            self.timer.singleShot(self.tps_between_two * 1000, self.measure) #On attent le temps programmé entre 2 intervals puis on relance measure()

    def set_parameters(self):
        if self.instrument_list[self.compteur_measure] == "Impédance": #Si on utilise l'analyseur de réseau vectoriel de Pavel
            window_VNA.sizeValue.setValue(self.parametre_list[self.compteur_measure][1])
            window_VNA.rateValue.setCurrentIndex(self.parametre_list[self.compteur_measure][2])
            window_VNA.startValue.setValue(self.parametre_list[self.compteur_measure][3])
            window_VNA.stopValue.setValue(self.parametre_list[self.compteur_measure][4])
            window_VNA.phase2Value.setValue(self.parametre_list[self.compteur_measure][5])
            window_VNA.phase1Value.setValue(self.parametre_list[self.compteur_measure][6])
            window_VNA.level1Value.setValue(self.parametre_list[self.compteur_measure][7])
            window_VNA.level2Value.setValue(self.parametre_list[self.compteur_measure][8])
            window_VNA.corrValue.setValue(self.parametre_list[self.compteur_measure][9])
            window_VNA.external_open = self.parametre_list[self.compteur_measure][10]
            window_VNA.external_short = self.parametre_list[self.compteur_measure][11]
            window_VNA.external_load = self.parametre_list[self.compteur_measure][12]

    def sweep(self):
        if self.instrument_list[self.compteur_measure] == "Impédance":
            window_VNA.sweep('dut') #On appelle le programme de Pavel pour effectuer le balayage en fréquence
        """if self.interface == "VNA_PyRpl":
            pyrpl_sweep_dut #Faire le sweep avec PyRpl"""

        self.timer.start(1) #On appelle is_data_ready() toute les 1ms

    #Arret total du data logger et de la mesure en cours
    def stop_data_logger(self):
        self.ui.pushButton_8.setEnabled(False)
        print("stop data_logger")
        self.is_acquisition_active = False
        self.timer.stop() #arret du Qtimer
        window_VNA.cancel() #arreter la mesure en cours
        self.stop_total_time_compteur = time.time()
        self.stop_time_compteur = time.time()
        #print("Temps total = " + str(self.stop_total_time_compteur - self.start_total_time_compteur) + " (s)")
        self.value = 0

    #Génération des données temporelle de la mesure
    def temporal_list(self, nb_point):
        nb_acquisiton = self.ui.doubleSpinBox_7.value()
        time_single_point = (self.stop_time_compteur - self.start_time_compteur) / nb_point #durée de la mesure d'un seul point
        compteur_time_single_point = 0 #Temps associé à chaque point
        self.list_time_single_mesure = [] #List du temps associé à chaque point de la mesure
        for point in range(0, nb_point): #pour chaque point on associé le moment qui lui correspond
            #self.start_time_compteur -> Début de la mesure
            #self.start_total_time_compteur -> Début de l'acquisition
            self.list_time_single_mesure.append((self.start_time_compteur - self.start_total_time_compteur) + compteur_time_single_point)
            compteur_time_single_point += time_single_point
        #print(self.list_time_single_mesure)

    #On enregistre les données au point txt (format csv), si le fichier exite déja on le remplace
    def save_data_text(self):
        if self.ui.lineEdit_2.text() == "":
            self.ui.lineEdit_2.setText(self.ui.comboBox.currentText())

        #Enregistrement frequenciel
        if os.path.exists(self.ui.lineEdit_5.text() + "/" + self.ui.lineEdit_2.text() + "_" + self.acquisition_measure_list[0][self.compteur_measure - 1] + ".txt"):
            if self.compteur_acquistion == 0 and self.compteur_measure == 1:
                mode_lecture = "w"
            else:
                mode_lecture = "a"
        else:
            mode_lecture = "w"

        if self.ui.lineEdit_2.text() != "":
            fichier = self.ui.lineEdit_5.text() + "/" + self.ui.lineEdit_2.text() + "_" + self.acquisition_measure_list[0][self.compteur_measure - 1] + ".txt"
            with open(fichier, mode_lecture) as data_file:
                if self.compteur_acquistion == 0:
                    data_file.write("%measure" + "\t" + "point" + "\t" + "Time (ms)" + "\t" + "Freq" + "\t" + "Module" + "\t" + "Phase" + "\t" + "Max_module_Freq" + "\t" + "Max_module" + "\t" + "Max_module_time" + "\t" + "Real" + "\t" + "Imag" + "\n")
                else:
                    if self.compteur_acquistion == 1 and self.compteur_measure == 0:
                        data_file.write("%measure" + "\t" + "point" + "\t" + "Time (ms)" + "\t" + "Freq" + "\t" + "Module" + "\t" + "Phase" + "\t" + "Max_module_Freq" + "\t" + "Max_module" + "\t" + "Max_module_time" + "\t" + "Real" + "\t" + "Imag" + "\n")
                for j in range (0, self.nb_point): # remplissage du tableau par bloc
                    #data_file.write(str(self.list_point_acqu[self.compteur_acquistion - 1][j])+"\t"+str(frequence[j])+"\t"+str(module[j])+"\t"+str(phase[j])+"\n")
                    if self.compteur_measure == 0  and self.compteur_measure == 1:
                        self.compteur_measure_save = self.nb_measure
                    else:
                        self.compteur_measure_save = self.compteur_measure
                    data_file.write(str(self.compteur_measure_save) + "\t" + str(j) + "\t" + str(self.meas_time[j]) + "\t" + str(self.meas_frequ[j]) + "\t" + str(self.meas_z_module[j]) + "\t" + str(self.meas_z_arg[j]) + "\t" + str(self.meas_z_module_max_freq) + "\t" + str(self.meas_z_module_max_value) + "\t" + str(self.meas_z_module_max_time) + "\t" + str(self.meas_z_real[j]) + "\t" + str(self.meas_z_imag[j]) + "\n")
                data_file.write("\n")
            #self.convertion_gnuplot() #Conversion des données au format Gnu Plot

        #Enregistrement temporel
        if self.ui.lineEdit_2.text() != "":
            if self.compteur_measure == 0: #Si compteur de mesure == 0, c'est peut etre qu'une acquisition viens de se terminer
                self.compteur_measure_save = self.nb_measure
            else:
                self.compteur_measure_save = self.compteur_measure
            if os.path.exists(self.ui.lineEdit_5.text() + "/" + self.ui.lineEdit_2.text() + "_evolution_" + self.acquisition_measure_list[0][self.compteur_measure_save - 1] +".txt"):
                if self.compteur_acquistion == 0  and self.compteur_measure == 1: #Si c'est la premiere fois que le fichier est modifié
                    mode_lecture = "w"
                else:
                    mode_lecture = "a"
            else:
                mode_lecture = "w"
            fichier = self.ui.lineEdit_5.text() + "/" + self.ui.lineEdit_2.text() + "_evolution_" + self.acquisition_measure_list[0][self.compteur_measure_save - 1] +".txt"
            with open(fichier, mode_lecture) as data_file:
                if self.compteur_acquistion == 0: #Si c'est la premiere fois que le fichier est modifié
                    data_file.write("%max_mod_evolution" + "\t" + "max_mod_freq_evolution" + "\t" + "max_mod_time_evolution" + "\t" + "max_arg_evolution" + "\t" + "max_arg_freq_evolution" + "\t" + "max_arg_time_evolution" + "\n")
                else:
                    if self.compteur_acquistion == 1 and self.compteur_measure == 0:
                        data_file.write("%max_mod_evolution" + "\t" + "max_mod_freq_evolution" + "\t" + "max_mod_time_evolution" + "\t" + "max_arg_evolution" + "\t" + "max_arg_freq_evolution" + "\t" + "max_arg_time_evolution" + "\n")
                data_file.write(str(self.meas_z_module_max_value) + "\t" + str(self.meas_z_module_max_freq) + "\t" + str(self.meas_z_module_max_time) + "\t" + str(self.meas_z_arg_max_value) + "\t" + str(self.meas_z_arg_max_freq) + "\t" + str(self.meas_z_arg_max_time) + "\n")
            #self.convertion_gnuplot() #Conversion des données au format Gnu Plot

    """def convertion_gnuplot(self):
        fichier2 =  self.ui.lineEdit_5.text() + "/" + self.ui.lineEdit_2.text() + ".txt"
        with open(fichier2, "a") as data_file_plt:
            data_file_plt.write("#Date d'acquisition : "+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"\n")
            data_file_plt.write("fichier ='"+self.ui.lineEdit_2.text()+".txt'"+"\n")
            data_file_plt.write("set y2tics"+"\n")
            data_file_plt.write("set ylabel 'A'"+"\n")
            data_file_plt.write("set y2label 'B'"+"\n")
            data_file_plt.write("set auto"+"\n")
            data_file_plt.write("plot fichier using 1:2 w l linetype 3 title 'A','' using 1:3 w l linetype 4 title 'B' axes x1y2"+"\n")"""

    #Lecture des données depuis le programme de Pavel
    def read_data(self):
        if self.instrument_list[self.compteur_measure - 1] == "Impédance":
            self.freq = window_VNA.dut.freq
            self.z = window_VNA.impedance(self.freq)
            self.nb_point = window_VNA.sizeValue.value()
            """if self.interface == "VNA_PyRpl":
                freq = pyrpl_freq
                z = pyrpl_z"""

        self.temporal_list(len(self.freq))

    def read_data_single(self):
        self.freq = window_VNA.dut.freq
        self.z = window_VNA.impedance(self.freq)
        self.nb_point = window_VNA.sizeValue.value()

    def process_data_single(self):
        self.meas_frequ = self.freq
        z = self.z
        self.meas_z = z
        self.meas_z_module = np.minimum(9.99e4, np.absolute(z))
        self.meas_z_arg = np.angle(z, deg = True)

    def read_data_osl(self):
                self.freq_open = window_VNA.open.freq
                self.freq_short = window_VNA.short.freq
                self.freq_load = window_VNA.load.freq

                self.open_data = window_VNA.interp(self.freq_open, window_VNA.open)
                self.short_data = window_VNA.interp(self.freq_short, window_VNA.short)
                self.load_data = window_VNA.interp(self.freq_load, window_VNA.load)

    def process_data(self, freq, z):
        self.meas_time = self.list_time_single_mesure
        self.meas_frequ = freq
        self.meas_z = z
        self.meas_z_module = np.minimum(9.99e4, np.absolute(z))
        self.meas_z_arg = np.angle(z, deg = True)
        self.meas_z_real = np.real(z)
        self.meas_z_imag = np.imag(z)

        #Calcul module maximum
        self.meas_z_module_max_value_index = self.meas_z_module.tolist().index(max(self.meas_z_module)) #tolist convertie le format de numpy en liste

        self.meas_z_module_max_value = max(self.meas_z_module)
        self.meas_z_module_max_freq = self.meas_frequ[self.meas_z_module_max_value_index]
        self.meas_z_module_max_time = self.meas_time[self.meas_z_module_max_value_index]

        #Calcul phase maximum
        self.meas_z_arg_max_value_index = self.meas_z_arg.tolist().index(max(self.meas_z_arg)) #tolist convertie le format de numpy en liste

        self.meas_z_arg_max_value = max(self.meas_z_arg)
        self.meas_z_arg_max_freq = self.meas_frequ[self.meas_z_arg_max_value_index]
        self.meas_z_arg_max_time = self.meas_time[self.meas_z_arg_max_value_index]

    def update_max_evolution_list(self):
        self.meas_z_max_evolution[self.compteur_measure - 1][0].append(self.meas_z_module_max_value)
        self.meas_z_max_evolution[self.compteur_measure - 1][1].append(self.meas_z_module_max_freq)
        self.meas_z_max_evolution[self.compteur_measure - 1][2].append(self.meas_z_module_max_time)
        self.meas_z_max_evolution[self.compteur_measure - 1][3].append(self.meas_z_arg_max_value)
        self.meas_z_max_evolution[self.compteur_measure - 1][4].append(self.meas_z_arg_max_freq)
        self.meas_z_max_evolution[self.compteur_measure - 1][5].append(self.meas_z_arg_max_time)

    def process_data_osl(self):
        self.z_module_open = np.minimum(9.99e4, np.absolute(self.open_data))
        self.z_module_short = np.minimum(9.99e4, np.absolute(self.short_data))
        self.z_module_load = np.minimum(9.99e4, np.absolute(self.load_data))
        self.z_arg_open = np.angle(self.open_data, deg = True)
        self.z_arg_short = np.angle(self.short_data, deg = True)
        self.z_arg_load = np.angle(self.load_data, deg = True)

    def view_and_save_data(self):
        self.actualise_current_data_plot()
        #View data
        label_x = self.ui.comboBox_4.currentText()
        label_y1 = self.ui.comboBox_3.currentText()
        label_y2 = self.ui.comboBox_5.currentText()
        x1= self.current_x1
        y1= self.current_y1
        x2= self.current_x2
        y2= self.current_y2

        self.plot_data(x1, y1, x2, y2, label_x, label_y1, label_y2) #Affichage graphique des données
        self.ui.label_7.setText(self.acquisition_measure_list[0][self.compteur_measure - 1])

        #Save data
        if self.ui.lineEdit_2.text() != "":
            self.save_data_pickle()
            self.save_data_text()

    #Affichage graphique des données
    def plot_data(self, x1, y1, x2, y2, x_label, y1_label, y2_label):
        if(self.p2):
            self.p2.clear()
        if(self.p1):
            self.p1.clear()
        self.ui.graphicsView_4.clear()

        self.p1 = self.ui.graphicsView_4.plotItem.plot(x1, y1, pen='b')
        self.ui.graphicsView_4.showAxis('right')
        self.p2 = pg.ViewBox()

        self.graph2 = self.ui.graphicsView_4.plotItem.scene().addItem(self.p2)

        self.ui.graphicsView_4.getAxis('right').linkToView(self.p2)
        self.p2.addItem(pg.PlotCurveItem(x2, y2, pen='r'))
        self.p2.setXLink(self.ui.graphicsView_4)
        self.ui.graphicsView_4.getAxis('right').setLabel(y2_label, color='#FF0000')
        self.ui.graphicsView_4.getAxis('left').setLabel(y1_label, color='#0000ff')
        self.ui.graphicsView_4.getAxis('bottom').setLabel(x_label, color='#ffffff')

        self.update_view()

        self.ui.graphicsView_4.plotItem.vb.sigResized.connect(self.update_view)
    #Gestion et actualisation de l'affichage graphique

    def plot_data_osl(self, x1, y1, x2, y2, x_label, y1_label, y2_label):
        """print(x1)
        print(x2)
        print(y1)
        print(y2)"""
        if(self.p2):
            self.p2.clear()
        if(self.p1):
            self.p1.clear()
        windows_Impedance.ui.graphicsView.clear()

        self.p1 = windows_Impedance.ui.graphicsView.plotItem.plot(x1, y1, pen='b')
        windows_Impedance.ui.graphicsView.showAxis('right')
        self.p2 = pg.ViewBox()

        self.graph2 = windows_Impedance.ui.graphicsView.plotItem.scene().addItem(self.p2)

        windows_Impedance.ui.graphicsView.getAxis('right').linkToView(self.p2)
        self.p2.addItem(pg.PlotCurveItem(x2, y2, pen='r'))
        self.p2.setXLink(windows_Impedance.ui.graphicsView)
        windows_Impedance.ui.graphicsView.getAxis('right').setLabel(y2_label, color='#FF0000')
        windows_Impedance.ui.graphicsView.getAxis('left').setLabel(y1_label, color='#0000ff')
        windows_Impedance.ui.graphicsView.getAxis('bottom').setLabel(x_label, color='#ffffff')

        self.update_view_osl()

        windows_Impedance.ui.graphicsView.plotItem.vb.sigResized.connect(self.update_view)

    #Gestion et actualisation de l'affichage graphique
    def update_view_osl(self):

        self.p2.setGeometry(windows_Impedance.ui.graphicsView.plotItem.vb.sceneBoundingRect())

        self.p2.linkedViewChanged(windows_Impedance.ui.graphicsView.plotItem.vb, self.p2.XAxis)

    def update_view(self):

        self.p2.setGeometry(self.ui.graphicsView_4.plotItem.vb.sceneBoundingRect())

        self.p2.linkedViewChanged(self.ui.graphicsView_4.plotItem.vb, self.p2.XAxis)

    #Sauvegarde des données(fréquence, impédance et phase) et des paramètres de configuration au format pickle
    def save_data_pickle(self):
        #On essai de récupérer les anciens chemins de stockage (sauvegarde) des config et des acquisitions
        self.donnees.append([self.meas_frequ, self.meas_z_module, self.meas_z_arg])
        with open(self.ui.lineEdit_5.text() + "/" + self.ui.lineEdit_2.text() + ".dlo", 'wb') as file_:
            #On sauvegarde d'abord les paramètres de configuration...
            pickle.dump(self.ui.doubleSpinBox_6.value(), file_)
            pickle.dump(self.ui.doubleSpinBox_7.value(), file_)
            pickle.dump(self.ui.doubleSpinBox_8.value(), file_)
            #...puis les données d'acquisition
            pickle.dump(self.donnees, file_)

        #debogage (Vérification du contenu du fichier de sauvegarde pickle)
        """with open(self.ui.lineEdit_5.text() + "/" + self.ui.lineEdit_2.text(), 'rb') as file_:
            print(pickle.load(file_))
            print(pickle.load(file_))
            print(pickle.load(file_))
            print(pickle.load(file_))"""

    #Sauvegarde la configuration courante dans un fichier config.bck à la racine du programme principal (data_logger.py)
    def actualise_save_config(self):
        with open("config.bck", 'wb') as file_:
            pickle.dump(self.ui.doubleSpinBox_6.value(), file_)
            pickle.dump(self.ui.doubleSpinBox_7.value(), file_)
            pickle.dump(self.ui.doubleSpinBox_8.value(), file_)
            pickle.dump(self.ui.lineEdit_5.text(), file_)

    def actualise_data_plot_list(self):
        list_freq = ["|z|", "Arg", "Real", "Imag"]
        list_time = ["|z|", "Arg", "Real", "Imag", "Max |z|", "Max |z| freq", "Max arg", "Max arg freq"]

        #Vidage de tous les éléments des comboBox 2 et 3
        self.ui.comboBox_3.clear()
        self.ui.comboBox_5.clear()

        if self.ui.comboBox_4.currentIndex() == 0: #Si mode temorelle
                self.ui.comboBox_3.addItems(list_freq)
                self.ui.comboBox_5.addItems(list_freq)
        else: #Si mode fréquentiel
                self.ui.comboBox_3.addItems(list_time)
                self.ui.comboBox_5.addItems(list_time)

    def actualise_current_data_plot(self):
        if self.ui.comboBox_4.currentText() == "Freq (Hz)":
            self.current_x1 = self.meas_frequ
            if self.ui.comboBox_3.currentText() == "|z|":
                self.current_y1 = self.meas_z_module
            if self.ui.comboBox_3.currentText() == "Arg":
                self.current_y1 = self.meas_z_arg
            if self.ui.comboBox_3.currentText() == "Real":
                self.current_y1 = self.meas_z_real
            if self.ui.comboBox_3.currentText() == "Imag":
                self.current_y1 = self.meas_z_imag

            self.current_x2 = self.meas_frequ
            if self.ui.comboBox_5.currentText() == "|z|":
                self.current_y2 = self.meas_z_module
            if self.ui.comboBox_5.currentText() == "Arg":
                self.current_y2 = self.meas_z_arg
            if self.ui.comboBox_5.currentText() == "Real":
                self.current_y2 = self.meas_z_real
            if self.ui.comboBox_5.currentText() == "Imag":
                self.current_y2 = self.meas_z_imag

        if self.ui.comboBox_4.currentText() == "Time (ms)":
            if self.ui.comboBox_3.currentText() == "|z|":
                self.current_y1 = self.meas_z_module
                self.current_x1 = self.meas_time
            if self.ui.comboBox_3.currentText() == "Arg":
                self.current_y1 = self.meas_z_arg
                self.current_x1 = self.meas_time
            if self.ui.comboBox_3.currentText() == "Real":
                self.current_y1 = self.meas_z_real
                self.current_x1 = self.meas_time
            if self.ui.comboBox_3.currentText() == "Imag":
                self.current_y1 = self.meas_z_imag
                self.current_x1 = self.meas_time

            if self.ui.comboBox_5.currentText() == "|z|":
                self.current_y2 = self.meas_z_module
                self.current_x2 = self.meas_time
            if self.ui.comboBox_5.currentText() == "Arg":
                self.current_y2 = self.meas_z_arg
                self.current_x2 = self.meas_time
            if self.ui.comboBox_5.currentText() == "Real":
                self.current_y2 = self.meas_z_real
                self.current_x2 = self.meas_time
            if self.ui.comboBox_5.currentText() == "Imag":
                self.current_y2 = self.meas_z_imag
                self.current_x2 = self.meas_time

            if self.ui.comboBox_3.currentText() == "Max |z|":
                self.current_y1 = self.meas_z_max_evolution[self.compteur_measure - 1][0]
                self.current_x1 = self.meas_z_max_evolution[self.compteur_measure - 1][2]
            if self.ui.comboBox_3.currentText() == "Max |z| freq":
                self.current_y1 = self.meas_z_max_evolution[self.compteur_measure - 1][1]
                self.current_x1 = self.meas_z_max_evolution[self.compteur_measure - 1][2]
            if self.ui.comboBox_3.currentText() == "Max arg":
                self.current_y1 = self.meas_z_max_evolution[self.compteur_measure - 1][3]
                self.current_x1 = self.meas_z_max_evolution[self.compteur_measure - 1][5]
            if self.ui.comboBox_3.currentText() == "Max arg freq":
                self.current_y1 = self.meas_z_max_evolution[self.compteur_measure - 1][4]
                self.current_x1 = self.meas_z_max_evolution[self.compteur_measure - 1][5]

            if self.ui.comboBox_5.currentText() == "Max |z|":
                self.current_y2 = self.meas_z_max_evolution[self.compteur_measure - 1][0]
                self.current_x2 = self.meas_z_max_evolution[self.compteur_measure - 1][2]
            if self.ui.comboBox_5.currentText() == "Max |z| freq":
                self.current_y2 = self.meas_z_max_evolution[self.compteur_measure - 1][1]
                self.current_x2 = self.meas_z_max_evolution[self.compteur_measure - 1][2]
            if self.ui.comboBox_5.currentText() == "Max arg":
                self.current_y2 = self.meas_z_max_evolution[self.compteur_measure - 1][3]
                self.current_x2 = self.meas_z_max_evolution[self.compteur_measure - 1][5]
            if self.ui.comboBox_5.currentText() == "Max arg freq":
                self.current_y2 = self.meas_z_max_evolution[self.compteur_measure - 1][4]
                self.current_x2 = self.meas_z_max_evolution[self.compteur_measure - 1][5]

    #Actualisation de la barre de progression de l'acquisition (en utilisant celle du programme de Pavel)
    def progress_bar(self, value):
        self.ui.progressBar_4.setMinimum(0)
        maxbar = 0
        for measure in self.parametre_list:
            maxbar += measure[1]

        self.ui.progressBar_4.setMaximum(maxbar * self.nb_acquisition)
        if value > self.sauv_value:
            self.value = maxbar * self.compteur_acquistion + self.compteur_measure * window_VNA.progressBar.maximum() + value
            self.ui.progressBar_4.setValue(self.value)
            self.sauv_value = value

    #Sélection du répertoire courant de travail
    def select_file(self):
        options = QFileDialog.Options()
        fileName = QFileDialog.getExistingDirectory(self,"QFileDialog.getExistingDirectory()", options=options)
        if fileName:
            self.ui.lineEdit_5.setText(fileName)
            #L'actualisation se fait automatiquement par le signal émis textChanged

    def active_start(self):
        self.ui.pushButton_7.setEnabled(True)

    def connection(self):
        window_VNA.socket.error.connect(self.deconnection)
        if self.connection == False:
            window_VNA.addrValue.setText(self.ui.lineEdit.text())
            self.ui.toolButton.setEnabled(False)
            self.ui.pushButton_7.setEnabled(True)
            window_VNA.start()
            self.connection = True
            self.ui.toolButton.setText("Deconnexion")
            self.ui.toolButton.setEnabled(True)
            windows_Impedance.ui.pushButton_19.setEnabled(True)
            windows_Impedance.ui.pushButton_20.setEnabled(True)
            windows_Impedance.ui.pushButton_21.setEnabled(True)

        else:
            self.deconnection()

    def deconnection(self):
        window_VNA.stop()
        self.ui.toolButton.setText("Connexion")
        self.connection = False
        windows_Impedance.ui.pushButton_19.setEnabled(False)
        windows_Impedance.ui.pushButton_20.setEnabled(False)
        windows_Impedance.ui.pushButton_21.setEnabled(False)
        self.ui.pushButton_7.setEnabled(False)
        self.ui.pushButton_9.setEnabled(False)

    def select_file_configuration(self):
        options = QFileDialog.Options()
        fileName = QFileDialog.getExistingDirectory(self,"QFileDialog.getExistingDirectory()", options=options)
        if fileName:
            self.ui.lineEdit_6.setText(fileName)
            #L'actualisation se fait automatiquement par le signal émis textChanged
            self.sauv_select_files()
            self.load_list_acquisition()

    def select_file_acquisition(self):
            options = QFileDialog.Options()
            fileName = QFileDialog.getExistingDirectory(self,"QFileDialog.getExistingDirectory()", options=options)
            if fileName:
                self.ui.lineEdit_5.setText(fileName)
                #L'actualisation se fait automatiquement par le signal émis textChanged
                self.sauv_select_files()

    def sauv_select_files(self):
        with open("config", 'wb') as file_:
            pickle.dump(self.ui.lineEdit_6.text(), file_)
            pickle.dump(self.ui.lineEdit_5.text(), file_)

    def open(self):
        self.sweep_osl = "open"
        self.charge_parametre_osl()
        window_VNA.progressBar.valueChanged[int].connect(self.set_progressbar_calibr)
        windows_Impedance.ui.pushButton_21.setEnabled(False)
        windows_Impedance.ui.pushButton_19.setEnabled(False)
        windows_Impedance.ui.pushButton_20.setEnabled(False)
        window_VNA.sweep('open')

    def short(self):
        self.sweep_osl = "short"
        self.charge_parametre_osl()
        window_VNA.progressBar.valueChanged[int].connect(self.set_progressbar_calibr)
        windows_Impedance.ui.pushButton_21.setEnabled(False)
        windows_Impedance.ui.pushButton_19.setEnabled(False)
        windows_Impedance.ui.pushButton_20.setEnabled(False)
        window_VNA.mode = 'short'
        window_VNA.sweep('short')
        #partial(window_VNA.sweep, 'short')

    def load(self):
        self.sweep_osl = "load"
        self.charge_parametre_osl()
        window_VNA.progressBar.valueChanged[int].connect(self.set_progressbar_calibr)
        windows_Impedance.ui.pushButton_21.setEnabled(False)
        windows_Impedance.ui.pushButton_19.setEnabled(False)
        windows_Impedance.ui.pushButton_20.setEnabled(False)
        window_VNA.sweep('load')

    def charge_parametre_osl(self):
            window_VNA.sizeValue.setValue(windows_Impedance.ui.spinBox_3.value())
            window_VNA.rateValue.setCurrentIndex(windows_Impedance.ui.comboBox_2.currentIndex())
            window_VNA.startValue.setValue(windows_Impedance.ui.spinBox.value())
            window_VNA.stopValue.setValue(windows_Impedance.ui.spinBox_2.value())
            window_VNA.phase2Value.setValue(windows_Impedance.ui.spinBox_15.value())
            window_VNA.phase1Value.setValue(windows_Impedance.ui.spinBox_13.value())
            window_VNA.level1Value.setValue(windows_Impedance.ui.spinBox_14.value())
            window_VNA.level2Value.setValue(windows_Impedance.ui.spinBox_16.value())
            window_VNA.corrValue.setValue(windows_Impedance.ui.spinBox_4.value())

    def set_progressbar_calibr(self):
        windows_Impedance.ui.progressBar.setMinimum(0)
        windows_Impedance.ui.progressBar.setMaximum(window_VNA.progressBar.maximum())
        windows_Impedance.ui.progressBar.setValue(window_VNA.progressBar.value() + 1)
        if window_VNA.reading == False: #Si la mesure est terminée
            self.read_data_osl()
            self.process_data_osl()

            if self.sweep_osl == "open":
                x1 = self.freq_open
                y1 = self.z_module_open
                x2 = x1
                y2 = self.z_arg_open
                label_x = "freq"
                label_y1 = "|z|"
                label_y2 = "Arg"
            if self.sweep_osl == "short":
                x1 = self.freq_short
                y1 = self.z_module_short
                x2 = x1
                y2 = self.z_arg_short
                label_x = "freq"
                label_y1 = "|z|"
                label_y2 = "Arg"
            if self.sweep_osl == "load":
                x1 = self.freq_load
                y1 = self.z_module_load
                x2 = x1
                y2 = self.z_arg_load
                label_x = "freq"
                label_y1 = "|z|"
                label_y2 = "Arg"

            self.plot_data_osl(x1, y1, x2, y2, label_x, label_y1, label_y2)
            windows_Impedance.ui.pushButton_21.setEnabled(True)
            windows_Impedance.ui.pushButton_19.setEnabled(True)
            windows_Impedance.ui.pushButton_20.setEnabled(True)

#actualise la liste python des acquisition en les récupérant dans l'arborescence.
    def actualise_acquisition_list(self):
        self.acquisition_list = []
        self.ensemble_item_acquisition = []
        for i in range(0, self.ui.treeWidget.topLevelItemCount()):
            self.acquisition_list.append(self.ui.treeWidget.topLevelItem(i).text(0))
            self.ensemble_item_acquisition.append(self.ui.treeWidget.topLevelItem(i))

        for i in range(0, self.ui.comboBox.count()):
            self.ui.comboBox.removeItem(0)

        for i in range(0, self.ui.treeWidget.topLevelItemCount()):
            self.ui.comboBox.addItem(self.acquisition_list[i])

    def add_acquisition(self):
        new_item = QTreeWidgetItem(["Acquisition" + str(self.ui.treeWidget.topLevelItemCount() + 1)])
        self.ui.treeWidget.addTopLevelItem(new_item)
        self.actualise_acquisition_list()

        #Ajout du fichier de config associé à l'acquisition ajoutée, représenté par un dossier acquisition'n'.
        try:
            os.mkdir(self.ui.lineEdit_6.text() + "/Acquisition" + str(self.ui.treeWidget.topLevelItemCount()))
        except OSError:
            pass
        with open(self.ui.lineEdit_6.text() + "/Acquisition" + str(self.ui.treeWidget.topLevelItemCount()) + "/config.acq", 'wb') as file_:
            pickle.dump(self.ui.doubleSpinBox_6.value(), file_)
            pickle.dump(self.ui.doubleSpinBox_7.value(), file_)
            pickle.dump(self.ui.doubleSpinBox_8.value(), file_)

    def load_list_acquisition(self):
        self.ui.treeWidget.clear()
        self.list_fichier_acquisition = os.listdir(self.ui.lineEdit_6.text())
        self.list_repertoire_acquisition = []
        for element in self.list_fichier_acquisition:
            if os.path.isdir(self.ui.lineEdit_6.text() + "/" + element):
                self.list_in_acquisition = os.listdir(self.ui.lineEdit_6.text() + "/" + element)
                isfichier_acquisition = False
                for fichier_dossier in self.list_in_acquisition:
                    if basename(fichier_dossier) == 'config.acq':
                        isfichier_acquisition = True
                if isfichier_acquisition == True:
                    self.list_repertoire_acquisition.append(basename(element))

        for acquisition in self.list_repertoire_acquisition:
            new_item = QTreeWidgetItem([acquisition])
            self.ui.treeWidget.addTopLevelItem(new_item)
        self.actualise_acquisition_list()

        i = 0
        for acquisition in self.list_repertoire_acquisition:
            list_fichier_mesure = os.listdir(self.ui.lineEdit_6.text() + "/" + acquisition)
            for fichier in list_fichier_mesure:
                fileName, fileExtension = os.path.splitext(self.ui.lineEdit_6.text() + "/" + acquisition + "/" + fichier)
                if fileExtension == '.msr':
                    new_measure = QTreeWidgetItem([basename(fileName)])
                    self.ui.treeWidget.topLevelItem(i).addChild(new_measure)
                    self.actualise_ensemble_measure()
            i += 1

        self.actualise_ensemble_measure()

    def add_measure(self):
        i = 1
        for item_acqu in self.acquisition_measure_list:
            for mesur in item_acqu:
                i += 1
        nb_element = i
        #print(nb_element)
        new_measure = QTreeWidgetItem(["measure" + str(nb_element)])
        self.current_acquisition.addChild(new_measure)
        self.actualise_ensemble_measure()
        self.sauv_param_impedance(self.ui.lineEdit_6.text() + "/" + self.current_acquisition.text(0) + "/" + "measure" + str(nb_element) + ".msr")

    def param_select_acquisition(self):
        list_select_item = self.ui.treeWidget.selectedItems()
        if list_select_item != []:
            self.select_acquisition(list_select_item[0])
        else:
            self.ui.pushButton_4.setEnabled(False)

    def select_acquisition(self, item):
        self.current_general_item = item
        self.ui.pushButton_3.setEnabled(True)
        if item in self.ensemble_item_acquisition:
            self.select_item = "acquisition"
            self.ui.pushButton_4.setEnabled(True)
            self.ui.pushButton_5.setEnabled(False)
            self.current_acquisition = item
            self.charge_acquistion(self.current_acquisition.text(0))
            self.ui.doubleSpinBox_6.setEnabled(True)
            self.ui.doubleSpinBox_7.setEnabled(True)
            self.ui.doubleSpinBox_8.setEnabled(True)
        else:
            self.select_item = "measure"
            self.current_measure_index = self.current_general_item.parent().indexOfChild(self.current_general_item)
            self.current_measure_parent = self.current_general_item.parent()
            self.current_acquisition = self.current_measure_parent
            self.ui.pushButton_4.setEnabled(False)
            self.ui.pushButton_5.setEnabled(True)
            self.ui.doubleSpinBox_6.setEnabled(False)
            self.ui.doubleSpinBox_7.setEnabled(False)
            self.ui.doubleSpinBox_8.setEnabled(False)

    def charge_acquistion(self, acquisition):
        #On complete les formulaire de saisi des paramètres enregistré dans le fichier de config de l'acquisition.
        with open(self.ui.lineEdit_6.text() + "/" + acquisition + "/config.acq", 'rb') as file_:
            self.ui.doubleSpinBox_6.setValue(pickle.load(file_))
            self.ui.doubleSpinBox_7.setValue(pickle.load(file_))
            self.ui.doubleSpinBox_8.setValue(pickle.load(file_))

        #On actualise le fichier de configuration de l'acquisition.
        with open(self.ui.lineEdit_6.text() + "/" + acquisition + "/config.acq", 'wb') as file_:
            pickle.dump(self.ui.doubleSpinBox_6.value(), file_)
            pickle.dump(self.ui.doubleSpinBox_7.value(), file_)
            pickle.dump(self.ui.doubleSpinBox_8.value(), file_)

    def actualise_param_acquisition(self):
        #On actualise le fichier de configuration de l'acquisition.
        with open(self.ui.lineEdit_6.text() + "/" + self.current_acquisition.text(0) + "/config.acq", 'wb') as file_:
            pickle.dump(self.ui.doubleSpinBox_6.value(), file_)
            pickle.dump(self.ui.doubleSpinBox_7.value(), file_)
            pickle.dump(self.ui.doubleSpinBox_8.value(), file_)

    def actualise_ensemble_measure(self):
        self.list_item_measure_acqu = []
        for item_acquisition in self.ensemble_item_acquisition:
            self.ensemble_item_measure = []
            for i in range(0, item_acquisition.childCount()):
                self.ensemble_item_measure.append(item_acquisition.child(i))
            self.list_item_measure_acqu.append([self.ensemble_item_measure])

        self.acquisition_measure_list = []

        for list_item_measure_acqu in self.list_item_measure_acqu:
            for list_item_measure in list_item_measure_acqu:
                self.list_measure_text = []
                for item_measure in list_item_measure:
                    self.list_measure_text.append(item_measure.text(0))
                self.acquisition_measure_list.append(self.list_measure_text)

    def remove_item(self):
        if self.ui.treeWidget.topLevelItemCount() > 0:
            if self.select_item == "acquisition":
                shutil.rmtree(self.ui.lineEdit_6.text() + "/" + self.current_general_item.text(0))
                self.ui.treeWidget.takeTopLevelItem(self.ui.treeWidget.indexOfTopLevelItem(self.current_general_item))
            if self.select_item == "measure":
                #print("path: " + self.ui.lineEdit_6.text() + "/" + self.current_general_item.parent().text(0) + "/" + self.current_general_item.text(0) + ".msr")
                os.remove(self.ui.lineEdit_6.text() + "/" + self.current_general_item.parent().text(0) + "/" + self.current_general_item.text(0) + ".msr")
                self.current_general_item.parent().takeChild(self.current_general_item.parent().indexOfChild(self.current_general_item))
            #+ selectionne un item si possible

            #+ suppression du fichier

            self.actualise_acquisition_list()

    def edit_measure(self):
        if self.ui.comboBox_2.currentText() == "Impédance":
            with open(self.ui.lineEdit_6.text() + "/" + self.current_measure_parent.text(0) + "/" + self.current_general_item.text(0) + ".msr", 'rb') as file_:
                instrument = pickle.load(file_)
                windows_Impedance.ui.spinBox_3.setValue(pickle.load(file_))
                windows_Impedance.ui.comboBox_2.setCurrentIndex(pickle.load(file_))
                windows_Impedance.ui.spinBox.setValue(pickle.load(file_))
                windows_Impedance.ui.spinBox_2.setValue(pickle.load(file_))
                windows_Impedance.ui.spinBox_15.setValue(pickle.load(file_))
                windows_Impedance.ui.spinBox_13.setValue(pickle.load(file_))
                windows_Impedance.ui.spinBox_14.setValue(pickle.load(file_))
                windows_Impedance.ui.spinBox_16.setValue(pickle.load(file_))
                windows_Impedance.ui.spinBox_4.setValue(pickle.load(file_))
            self.affiche_impedance()

    def pause_acquisition(self):
        if self.is_pause == False: #On est en continu, on se met en pause
            self.is_pause = True
            self.ui.pushButton_9.setText("Resume")
        else: #On est déja en pause, on se met en continu
            self.is_pause = False
            self.ui.pushButton_9.setText("Pause")

class Impedance(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Impedance, self).__init__(parent=parent)
        self.ui = Ui_MainWindow_impedance()
        self.ui.setupUi(self)

#Initialisation, lancemement, gestion et affichage de l'application
if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    app = QApplication(sys.argv)
    windows_data_logger = Data_logger()
    window_VNA = VNA()
    windows_Impedance = Impedance()
    window_VNA.update_tab()
    windows_data_logger.show()
    #window_VNA.show()
    sys.exit(app.exec())
