#!/usr/bin/env python
# -*- coding: utf-8 -*-
import ctypes
import inspect
import os
import re
import sys
import threading
import traceback

import keyboard
import pinyin
import PyQt5
import yaml
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtCore import QStringListModel
from PyQt5.QtWidgets import *

from testoutput import *
from utils.ui import ExtendedComboBox

if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    PyQt5.QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


class Ui(QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('ui/main_chs.ui', self)

        self.run_status = False

        keyboard.add_hotkey("ctrl+q", self.script_exit, suppress=True)

        self.trans = QtCore.QTranslator()
        if __import__('locale').getdefaultlocale()[0] == 'zh_CN':
            self.ui_lang = 'chs'
        else:
            self.ui_lang = 'chs'


        self.total_w = self.findChild(QSpinBox,"total_w")
        self.port_w = self.findChild(QSpinBox,"port_w")
        self.port_l = self.findChild(QSpinBox,"port_l")
        #self.nports = self.findChild(QSpinBox,"nports")
        self.Npml = self.findChild(QSpinBox,"Npml")
        #self. = self.findChild(QSpinBox,"")

        self.width_margin = self.findChild(QSpinBox,"width_margin")
        self.pass_min = self.findChild(QSpinBox,"pass_min")

        self.mode=self.findChild(QComboBox,"mode")
        self.mode.addItem('training')
        self.mode.addItem('simulation')
        self.mode.addItem('design')

        self.training_th=self.findChild(QLineEdit,"training_th")


        self.wl1=self.findChild(QLineEdit,"wl1")
        self.wl2=self.findChild(QLineEdit,"wl2")

        self.step_max = self.findChild(QSpinBox,"step_max")

        self.save = self.findChild(QPushButton, 'save')  # Find the button
        self.save.clicked.connect(self.saveButtonPressed)  # Click event
        self.run = self.findChild(QPushButton, 'run')  # Find the button
        self.run.clicked.connect(self.runButtonPressed)  # Click event
        self.load = self.findChild(QPushButton, 'load')  # Find the button
        self.load.clicked.connect(self.loadButtonPressed)  # Click event





        self.config = {}
        
        self.load_config('config/default.yaml')

        self.show()
        #if self.ui_lang == 'eng':
        #    self.tiggerEnglish()


    def triggerChinese(self):
        self.trans.load("ui/main_chs")
        # get app instance and load trans
        QApplication.instance().installTranslator(self.trans)
        # translate
        # self.retranslateUi()
        self.show()
        self.ui_lang = 'chs'
        

    def loadButtonPressed(self):
        load_path = QtWidgets.QFileDialog.getOpenFileName(self, "Load Config", "config", "YAML Config(*.yaml)")[0]
        if load_path == '':
            load_path = 'config/default.yaml'
        self.load_config(load_path)



    def load_config(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except:
            return QMessageBox.critical(self, 'Error!', "Load Path Fail", QMessageBox.Ok, QMessageBox.Ok)

        for k, v in self.config.items():
            if k == 'total_w':
                self.total_w.setValue(v)
            if k == 'port_l':
                self.port_l.setValue(v)
            if k == 'port_w':
                self.port_w.setValue(v)
            #if k == 'nports':
            #    self.nports.setValue(v)
            if k == 'width_margin':
                self.width_margin.setValue(v)
            if k == 'pass_min':
                self.pass_min.setValue(v)            
            if k == "mode" :
                self.mode.setCurrentText(f"{v}")
            if k == "step_max" :
                self.step_max.setValue(v)            
            if k == "training_th" :
                self.training_th.setText((v))              
            if k == "wl1" :
                self.wl1.setText((v))
            if k == "wl2" :
                self.wl2.setText((v))    
            if k == "Npml" :
                self.Npml.setValue((v))             

    def save_config(self):
        self.config['total_w'] = self.total_w.value()
        self.config['port_l'] = self.port_l.value()
        # self.config['reward_count'] = self.reward_count.value()
        self.config['port_w'] = self.port_w.value()
        self.config['Npml'] = self.Npml.value()
        self.config['pass_min'] = self.pass_min.value()
        self.config['width_margin'] = self.width_margin.value()
        #self.config['nports'] = self.nports.value()

        self.config['mode'] = self.mode.currentText()
        self.config['step_max'] = self.step_max.value()
        self.config['training_th'] = self.training_th.text()
        self.config['wl1'] = self.wl1.text()
        self.config['wl2'] = self.wl2.text()  



    def saveButtonPressed(self):
        self.save_config()
        save_path = QtWidgets.QFileDialog.getSaveFileName(self, 'Save To', "config", "YAML Config (*.yaml)")[0]
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f)
            print(self.config)
        except:
            return QMessageBox.critical(self, 'Error!', "Save Path Fail", QMessageBox.Ok, QMessageBox.Ok)

    def runButtonPressed(self):
        if not self.run_status:
            hero_text = ""
            

            self.save_config()
            cfm_text = f'''
                Current Setting:\n
                Total length: {self.config['total_w']}\n
                Port lenght: {self.config['port_l']}\n
                Port width: {self.config['port_w']}\n
            '''.strip().replace('    ', '')

            reply = QMessageBox.question(self, 'CONFIRM', cfm_text, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.run_status = True
                
                self.run.setText("Stop" if self.ui_lang == 'chs' else "Stop")
                self.script_run()
                #try:
                #    self._thread = threading.Thread(target=self.script_run)
                #    self._thread.start()
                #except Exception as e:
                #    print(f'catch that {e}')
            else:
                pass
        else:
            self.script_exit()

    def script_exit(self):
        if self.run_status:
            self.run.setText("run" if self.ui_lang == 'chs' else "Run")
            self.run_status = False
            plt.close()
            #stop_thread(self._thread)
        else:
            pass

    def script_run(self):
        try:
            run_from_gui(self.config)
        except Exception as e:
            print(e)
            self.run.setText("run" if self.ui_lang == 'chs' else "Run")
            self.run_status = False
            err_log = traceback.format_exc()
            with open('error.log', 'a+') as f:
                f.writelines(err_log + '\n')

    def closeEvent(self, event):
        self.script_exit()
        event.accept()

    

if __name__ == '__main__':
    os.chdir(os.path.abspath(os.path.dirname(os.path.realpath(__file__))))
    app = QApplication(sys.argv)
    window = Ui()
    app.exec_()
