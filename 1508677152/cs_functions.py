from aqt.qt import *
from aqt import mw
import re

#This code is a workaround to allow for non-sequential Cloze deletions (e.g., C1 follows C1)
#using a shortcut that doesn't need the alt button. The original Anki 2.1 code wouldn't play nicely otherwise. 
#Joseph removed the tooltip warning that was part of the original code below
def cs_editor_onAltCloze(self):
    self.saveNow(self._onAltCloze, keepFocus=True)

def cs_uEditor_onAltCloze(self):
    highest = 0
    for name, val in list(self.note.items()):
        m = re.findall(r"\{\{c(\d+)::", val)
        if m:
            highest = max(highest, sorted([int(x) for x in m])[-1])
        # reuse last?
    highest = max(1, highest)
    self.web.eval("wrap('{{c%d::', '}}');" % highest)

#Mimics the style of other Anki functions, analogue of customPaste
#Note that the saveNow function used earler takes the cursor to the end of the line,
#as it is meant to save work before entering a new window
def cs_editor_custom_paste(self):
    self._customPaste()

#Mimics the style of other Anki functions, analogue of _customPaste
def cs_uEditor_custom_paste(self):
    html = config_scuts["Ω custom paste text"]
    if config_scuts["Ω custom paste end style"].upper() == "Y":
        html += "</span>\u200b"
    with warnings.catch_warnings() as w:
        warnings.simplefilter('ignore', UserWarning)
        html = str(BeautifulSoup(html, "html.parser"))
    self.doPaste(html,True,True)

                        
#Converts json shortcuts into functions for the reviewer
#sToF: shortcutToFunction
def review_sToF(self,scut):
    #"reviewer" is retained for copy-pastability, may be removed later
    # "self.mw.onEditCurrent" is exactly how it was in reviewer.py, DO NOT CHANGE
    sdict = {
        "reviewer edit current": self.mw.onEditCurrent,
        "reviewer flip card": self.onEnterKey,
        "reviewer flip card 1": self.onEnterKey,
        "reviewer flip card 2": self.onEnterKey,
        "reviewer flip card 3": self.onEnterKey,
        "reviewer options menu": self.onOptions,
        "reviewer record voice": self.onRecordVoice,
        "reviewer play recorded voice": self.onReplayRecorded,
        "reviewer play recorded voice 1": self.onReplayRecorded,
        "reviewer play recorded voice 2": self.onReplayRecorded,
        "reviewer delete note": self.onDelete,
        "reviewer suspend card": self.onSuspendCard,
        "reviewer suspend note": self.onSuspend,
        "reviewer bury card": self.onBuryCard,
        "reviewer bury note": self.onBuryNote,
        "reviewer mark card": self.onMark,
        "reviewer set flag 1": lambda: self.setFlag(1),
        "reviewer set flag 2": lambda: self.setFlag(2),
        "reviewer set flag 3": lambda: self.setFlag(3),
        "reviewer set flag 4": lambda: self.setFlag(4),
        "reviewer set flag 0": lambda: self.setFlag(0),
        "reviewer replay audio": self.replayAudio,
        "reviewer choice 1": lambda: self._answerCard(1),
        "reviewer choice 2": lambda: self._answerCard(2),
        "reviewer choice 3": lambda: self._answerCard(3),
        "reviewer choice 4": lambda: self._answerCard(4),
    }
    return sdict[scut]

