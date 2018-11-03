#################################################
Version Data logger 2.0
#################################################

Descriptif de Version:

Version permettant l'utilisation d'un data logger pour l'automatisation d'acquisition déstinées à l'analyse d'impédance avec une Red Pitaya.
L'interface pour le paramétrage des mesures à été réalisé par Pavel et est gérée par le data logger (data_logger.py).
Les paramètres de chaque mesure peuvent être enregistré par l'interface de Pavel (Pour plus de détail consulté la documentation: http://pavel-demin.github.io/red-pitaya-notes/vna/).
Les paramètres de chaque acquisition (ensemble des mesures réalisées par le data logger après l'appuis sur le bouton Start) sont enregistrés dans le répertoire spécifié avec le nom désiré (Filename).
Chacune des configuration peuvent être rechargé pour une utilisation future. La dernière configuration du data logger est celle chargée par défault.
Les données d'acquisition sont enregistrées dans le même fichier que celui des configurations du data logger. Un fichier .txt est également géneré et contient l'ensemble des données au format csv (traçable par exemple par Gnu Plot ou lisible par Exel).

#################################################

Descriptif des fichiers requis:

data_logger.py: Programme principal du data logger.
UImainwindow.py: Interface graphique du data logger.
vna_2_2_1.py: Programme d'analyse vectoriel d'impédance de Pavel.
vna.ui: Interface graphique du programme précédant.
vna.ini: Fichier de configuration du programme de Pavel.

#################################################

Installations requises:
- Python3 avec librairie:
  pyqt5
  warnings
  sys
  time
  pyqtgraph
  pickle
  os

#################################################

Lancement du data logger:

Le data logger peut s'executer par un double-clique sur data_logger.py (Il faudra bien entendu que les .py soit liés à python3 (voir paragraphe précédant: Installations requises)).
