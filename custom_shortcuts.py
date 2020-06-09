# Mode: Python; coding: utf-8
#GODMODE Cloze and Custom Keyboard Shortcuts
#Code compiled by Joseph Yasmeh for Anki 2.1 on Mac on April 2019.
#My main contribution to this code is figuring out how to disable unneccessary tooltip notifications, how to get answer shortcuts to flip the card without moving to the next card, and how to merge a couple addons into one, so that they work together.
#
#The code for shortcuts is by Liresol (erichu264@gmail.com), from the addon Customize Keyboard Shortcuts
#I attempted to make GODMODE with its own limited shortcuts, but found that it interfered the above addon.
#So the easiest solution for me was to merge the two addons into one so that they don't conflict.
#
#The code for automatic note type switching is not my own. Credit goes to:
#Hyun Woo Park (phu54321@naver.com),
#Roland Sieker (ospalh@gmail.com), and
#Steve AW (steveawa@gmail.com)
#
#The above authors made their code free to use and modify under GNU GPL. This code is too.
#
#To learn how to make "monkey patch" add-ons, see https://apps.ankiweb.net/docs/addons.html#monkey-patching-and-method-wrapping
#
#CHANGELOG
#July 17 2019: Edited "reviewer choice" in config.json to fix a bug where 1234 was set to flip cards (and then #always rate as good) rather than rate them as hard, good, or easy.
#August 17 2019: Edited "window_browser add note" config.json to fix a bug where Ctrl+E would not make a new Cloze when the browser was open, given that shortcut was also being used for adding a card when the browser is open.
#January 28 2020: Fixed a bug only some users saw on Mac and Windows where cards could not be added. Removed global references, which were not being acknowledged for some users. Fixed a Python "TypeError" in the function "change_model_to."
#June 9 2020: Updated to cs_toolbarCenterLinks to work with Anki versions above 2.21. The function it referred to was changed in Anki, so I changed the syntax to match it.

########################################################################
#SECTION 1
#Telling the software what to import. Some of these are redundant because I'm copying and pasting my old code.
########################################################################
from aqt import mw
from aqt.qt import *
from anki.hooks import runHook,addHook
from aqt.utils import showWarning
from aqt.toolbar import Toolbar
from aqt.editor import Editor,EditorWebView
from aqt.reviewer import Reviewer
from anki.utils import json
from bs4 import BeautifulSoup
import warnings
from . import cs_functions as functions
from aqt import mw
from aqt.addcards import AddCards
from anki.hooks import wrap
from anki.hooks import addHook, runHook
from aqt.utils import tooltip
from anki.lang import _
from anki import version
import re
from aqt.utils import tooltip, showInfo
from anki.hooks import wrap
import aqt.editor
from aqt.editor import *



########################################################################
#SECTION 2
#Redefining how Anki deals with Cloze creation
#Deleted the tooltip warning given it is now redundant
#I tried to use the method of saving the original code and calling a custom version, as mentioned monkey patching section of the Anki 2.1 addon creation documentation
#But the code wouldn't work. So if something breaks with the addon in future Anki versions, look here and in section 5.
########################################################################
def onClozeADDON(self):
	self.saveNow(self._onCloze, keepFocus=True)

Editor.onCloze = onClozeADDON

def _onClozeADDON(self):
	highest = 0
	for name, val in list(self.note.items()):
		m = re.findall(r"\{\{c(\d+)::", val)
		if m:
			highest = max(highest, sorted([int(x) for x in m])[-1])
	# reuse last
	if not self.mw.app.keyboardModifiers() & Qt.ShiftModifier:
		highest += 1
	# must start at 1
	highest = max(1, highest)
	self.web.eval("wrap('{{c%d::', '}}');" % highest)

Editor._onCloze = _onClozeADDON



########################################################################
#SECTION 3
#This section of code does the automatic note type switching.
########################################################################

def modelExists(model_name):
    return bool(mw.col.models.byName(model_name))

def findModelName():
    basic_note_type = list(filter(modelExists, ['Basic', _('Basic')]))
    cloze_note_type = list(filter(modelExists, ['Cloze', _('Cloze')]))

    if not basic_note_type:
        tooltip('[Automatic basic to cloze] Cannot find source \'Basic\' model')
        basic_note_type = None

    if not cloze_note_type:
        tooltip('[Automatic basic to cloze] Cannot find target \'Cloze\' model')
        cloze_note_type = None
    else:
        cloze_note_type = cloze_note_type[0]

addHook("profileLoaded", findModelName)

#This function changes the models (note types).
# TypeError fixed an older bug from the newAddCards function, where Python got upset that ModelName was set equal to none.
def change_model_to(chooser, model_name):
    """Change to model with name model_name"""
    # Mostly just a copy and paste from the bottom of onModelChange()
    m = chooser.deck.models.byName(model_name)
    try:
        chooser.deck.conf['curModel'] = m['id']
    except TypeError:
        return
    cdeck = chooser.deck.decks.current()
    cdeck['mid'] = m['id']
    chooser.deck.decks.save(cdeck)
    runHook("currentModelChanged")
    chooser.mw.reset()

def isClozeNote(note):
    for name, val in note.items():
        if re.search(r'\{\{c(\d+)::', val):
            return True
    return False

#If you don't use this, tags won't save when models switch.
def callWithCallback(f, cb):
        f(cb)

#Joseph changed the tooltip notification to "Added" to remove the unneccesary warning note type switching.
#Also set modelchooser to go to specific note type names. This fixed a bug some users had.
def newAddCards(self, _old):
    note = self.editor.note
    basic_note_type = list(filter(modelExists, ['Basic', _('Basic')]))
    cloze_note_type = list(filter(modelExists, ['Cloze', _('Cloze')]))

    if not (basic_note_type and cloze_note_type):
        return _old(self)
    if note.model()['name'] in basic_note_type and isClozeNote(note):
        def cb1():
            change_model_to(self.modelChooser, 'Cloze')
            callWithCallback(self.editor.saveNow, cb2)
        def cb2():
            self._addCards()
            change_model_to(self.modelChooser, 'Basic')
            tooltip(_("Added"), period=500)
        callWithCallback(self.editor.saveNow, cb1)
    else:
        return _old(self)

AddCards.addCards = wrap(AddCards.addCards, newAddCards, "around")

#This disables the prompt for changing the note type.
#I deleted the block of code that checks if the card type is set to Cloze.
def addNoteADDON(self, note):
        note.model()['did'] = self.deckChooser.selectedId()
        ret = note.dupeOrEmpty()
        if ret == 1:
            showWarning(_(
                "The first field is empty."),
                help="AddItems#AddError")
            return
        cards = self.mw.col.addNote(note)
        if not cards:
            showWarning(_("""\
The input you have provided would make an empty \
question on all cards."""), help="AddItems")
            return None
        self.addHistory(note)
        self.mw.requireReset()
        return note

AddCards.addNote = addNoteADDON



########################################################################
#SECTION 4
#This section is from the add-on Customize Keyboard Shortcuts
########################################################################
#Gets config.json as config
config = mw.addonManager.getConfig(__name__)
CS_CONFLICTSTR = "Custom Shortcut Conflicts: \n\n"
#config_scuts initialized after cs_traverseKeys
Qt_functions = {"Qt.Key_Enter":Qt.Key_Enter,
                "Qt.Key_Return":Qt.Key_Return,
                "Qt.Key_Escape":Qt.Key_Escape,
                "Qt.Key_Space":Qt.Key_Space,
                "Qt.Key_Tab":Qt.Key_Tab,
                "Qt.Key_Backspace":Qt.Key_Backspace,
                "Qt.Key_Delete":Qt.Key_Delete,
                "Qt.Key_Left":Qt.Key_Left,
                "Qt.Key_Down":Qt.Key_Down,
                "Qt.Key_Right":Qt.Key_Right,
                "Qt.Key_Up":Qt.Key_Up,
                "Qt.Key_PageUp":Qt.Key_PageUp,
                "Qt.Key_PageDown":Qt.Key_PageDown,
                "<nop>":""
                }

#There is a weird interaction with QShortcuts wherein if there are 2 (or more)
#QShortcuts mapped to the same key and function and both are enabled,
#the shortcut doesn't work

#Part of this code exploits that by adding QShortcuts mapped to the defaults
#and activating/deactivating them to deactivate/activate default shortcuts

#There isn't an obvious way to get the original QShortcut objects, as
#The addons executes after the setup phase (which creates QShortcut objects)

def cs_traverseKeys(Rep, D):
    ret = {}
    for key in D:
        if isinstance(D[key],dict):
            ret[key] = cs_traverseKeys(Rep,D[key])
        elif D[key] not in Rep:
            ret[key] = D[key]
        else:
            ret[key] = Rep[D[key]]
    return ret

config_scuts = cs_traverseKeys(Qt_functions,config)

#This is the worst code I think I've written for custom-shortcuts
#Since QShortcuts cannot reveal their action (to the best of my knowledge),
#This map reconstructs what each QShortcut is supposed to do from its id
#The ids were found manually and are thus incredibly dubious
id_main_config = {-1: "main debug",
                  -2: "main deckbrowser",
                  -3: "main study",
                  -4: "main add",
                  -5: "main browse",
                  -6: "main stats",
                  -7: "main sync"
                  }

#Finds all the shortcuts, figures out relevant ones from hardcoded id check,
#and sets it to the right one
#This function has a side effect of changing the shortcut's id
def cs_main_setupShortcuts():
    qshortcuts = mw.findChildren(QShortcut)
    for scut in qshortcuts:
        if scut.id() in id_main_config:
            scut.setKey(config_scuts[id_main_config[scut.id()]])


#Governs the shortcuts on the main toolbar
def cs_mt_setupShortcuts():
    m = mw.form
    #Goes through and includes anything on the duplicates list
    scuts_list = {
        "m_toolbox quit": [config_scuts["m_toolbox quit"]],
        "m_toolbox preferences": [config_scuts["m_toolbox preferences"]],
        "m_toolbox undo": [config_scuts["m_toolbox undo"]],
        "m_toolbox see documentation": [config_scuts["m_toolbox see documentation"]],
        "m_toolbox switch profile": [config_scuts["m_toolbox switch profile"]],
        "m_toolbox export": [config_scuts["m_toolbox export"]],
        "m_toolbox import": [config_scuts["m_toolbox import"]],
        "m_toolbox study": [config_scuts["m_toolbox study"]],
        "m_toolbox create filtered deck": [config_scuts["m_toolbox create filtered deck"]],
        "m_toolbox addons": [config_scuts["m_toolbox addons"]]
    }
    for act,key in config_scuts["m_toolbox _duplicates"].items():
        scuts_list[act].append(key)
    m.actionExit.setShortcuts(scuts_list["m_toolbox quit"])
    m.actionPreferences.setShortcuts(scuts_list["m_toolbox preferences"])
    m.actionUndo.setShortcuts(scuts_list["m_toolbox undo"])
    m.actionDocumentation.setShortcuts(scuts_list["m_toolbox see documentation"])
    m.actionSwitchProfile.setShortcuts(scuts_list["m_toolbox switch profile"])
    m.actionExport.setShortcuts(scuts_list["m_toolbox export"])
    m.actionImport.setShortcuts(scuts_list["m_toolbox import"])
    m.actionStudyDeck.setShortcuts(scuts_list["m_toolbox study"])
    m.actionCreateFiltered.setShortcuts(scuts_list["m_toolbox create filtered deck"])
    m.actionAdd_ons.setShortcuts(scuts_list["m_toolbox addons"])

#Governs the shortcuts on the review window
def cs_review_setupShortcuts(self):
    dupes = []
    ret = [
        (config_scuts["reviewer edit current"], self.mw.onEditCurrent),
        (config_scuts["reviewer flip card 1"], self.onEnterKey),
        (config_scuts["reviewer flip card 2"], self.onEnterKey),
        (config_scuts["reviewer flip card 3"], self.onEnterKey),
        (config_scuts["reviewer replay audio 1"], self.replayAudio),
        (config_scuts["reviewer replay audio 2"], self.replayAudio),
        (config_scuts["reviewer set flag 1"], lambda: self.setFlag(1)),
        (config_scuts["reviewer set flag 2"], lambda: self.setFlag(2)),
        (config_scuts["reviewer set flag 3"], lambda: self.setFlag(3)),
        (config_scuts["reviewer set flag 4"], lambda: self.setFlag(4)),
        (config_scuts["reviewer set flag 0"], lambda: self.setFlag(0)),
        (config_scuts["reviewer mark card"], self.onMark),
        (config_scuts["reviewer bury note"], self.onBuryNote),
        (config_scuts["reviewer bury card"], self.onBuryCard),
        (config_scuts["reviewer suspend note"], self.onSuspend),
        (config_scuts["reviewer suspend card"], self.onSuspendCard),
        (config_scuts["reviewer delete note"], self.onDelete),
        (config_scuts["reviewer play recorded voice"], self.onReplayRecorded),
        (config_scuts["reviewer record voice"], self.onRecordVoice),
        (config_scuts["reviewer options menu"], self.onOptions),
        (config_scuts["reviewer choice 1"], lambda: self._answerCard(1)),
        (config_scuts["reviewer choice 2"], lambda: self._answerCard(2)),
        (config_scuts["reviewer choice 3"], lambda: self._answerCard(3)),
        (config_scuts["reviewer choice 4"], lambda: self._answerCard(4)),
    ]
    for scut in config_scuts["reviewer _duplicates"]:
        dupes.append((config_scuts["reviewer _duplicates"][scut],self.sToF(scut)))
    return dupes + ret

#The function to setup shortcuts on the Editor
#Something funky is going on with the default MathJax and LaTeX shortcuts
#It does not affect the function (as I currently know of)
def cs_editor_setupShortcuts(self):
    # if a third element is provided, enable shortcut even when no field selected
    cuts = [
        (config_scuts["editor card layout"], self.onCardLayout, True),
        (config_scuts["editor bold"], self.toggleBold),
        (config_scuts["editor italic"], self.toggleItalic),
        (config_scuts["editor underline"], self.toggleUnderline),
        (config_scuts["editor superscript"], self.toggleSuper),
        (config_scuts["editor subscript"], self.toggleSub),
        (config_scuts["editor remove format"], self.removeFormat),
        (config_scuts["editor foreground"], self.onForeground),
        (config_scuts["editor change col"], self.onChangeCol),
        (config_scuts["editor cloze"], self.onCloze),
        (config_scuts["editor cloze alt"], self.onAltCloze),
        (config_scuts["editor add media"], self.onAddMedia),
        (config_scuts["editor record sound"], self.onRecSound),
        (config_scuts["editor insert latex"], self.insertLatex),
        (config_scuts["editor insert latex equation"], self.insertLatexEqn),
        (config_scuts["editor insert latex math environment"], self.insertLatexMathEnv),
        (config_scuts["editor insert mathjax inline"], self.insertMathjaxInline),
        (config_scuts["editor insert mathjax block"], self.insertMathjaxBlock),
        (config_scuts["editor insert mathjax chemistry"], self.insertMathjaxChemistry),
        (config_scuts["editor html edit"], self.onHtmlEdit),
        (config_scuts["editor focus tags"], self.onFocusTags, True),
        (config_scuts["editor _extras"]["paste custom text"], self.customPaste)
    ]
    runHook("setupEditorShortcuts", cuts, self)
    for row in cuts:
        if len(row) == 2:
            keys, fn = row
            fn = self._addFocusCheck(fn)
        else:
            keys, fn, _ = row
        scut = QShortcut(QKeySequence(keys), self.widget, activated=fn)

#IMPLEMENTS Browser shortcuts
def cs_browser_setupShortcuts(self):
    f = self.form
    f.previewButton.setShortcut(config_scuts["window_browser preview"])
    f.actionReschedule.setShortcut(config_scuts["window_browser reschedule"])
    f.actionSelectAll.setShortcut(config_scuts["window_browser select all"])
    f.actionUndo.setShortcut(config_scuts["window_browser undo"])
    f.actionInvertSelection.setShortcut(config_scuts["window_browser invert selection"])
    f.actionFind.setShortcut(config_scuts["window_browser find"])
    f.actionNote.setShortcut(config_scuts["window_browser goto note"])
    f.actionNextCard.setShortcut(config_scuts["window_browser goto next note"])
    f.actionPreviousCard.setShortcut(config_scuts["window_browser goto previous note"])
    f.actionChangeModel.setShortcut(config_scuts["window_browser change note type"])
    f.actionGuide.setShortcut(config_scuts["window_browser guide"])
    f.actionFindReplace.setShortcut(config_scuts["window_browser find and replace"])
    f.actionTags.setShortcut(config_scuts["window_browser filter"])
    f.actionCardList.setShortcut(config_scuts["window_browser goto card list"])
    f.actionReposition.setShortcut(config_scuts["window_browser reposition"])
    f.actionFirstCard.setShortcut(config_scuts["window_browser first card"])
    f.actionLastCard.setShortcut(config_scuts["window_browser last card"])
    f.actionClose.setShortcut(config_scuts["window_browser close"])
    f.action_Info.setShortcut(config_scuts["window_browser info"])
    f.actionAdd_Tags.setShortcut(config_scuts["window_browser add tag"])
    f.actionRemove_Tags.setShortcut(config_scuts["window_browser remove tag"])
    f.actionToggle_Suspend.setShortcut(config_scuts["window_browser suspend"])
    f.actionDelete.setShortcut(config_scuts["window_browser delete"])
    f.actionAdd.setShortcut(config_scuts["window_browser add note"])
    f.actionChange_Deck.setShortcut(config_scuts["window_browser change deck"])
    f.actionRed_Flag.setShortcut(config_scuts["window_browser flag_red"])
    try:
        f.actionOrange_Flag.setShortcut(config_scuts["window_browser flag_orange"])
    except AttributeError:
        f.actionPurple_Flag.setShortcut(config_scuts["window_browser flag_orange"])
    f.actionGreen_Flag.setShortcut(config_scuts["window_browser flag_green"])
    f.actionBlue_Flag.setShortcut(config_scuts["window_browser flag_blue"])
    f.actionSidebar.setShortcut(config_scuts["window_browser goto sidebar"])
    f.actionToggle_Mark.setShortcut(config_scuts["window_browser toggle mark"])
    f.actionClear_Unused_Tags.setShortcut(config_scuts["window_browser clear unused tags"])
    f.actionFindDuplicates.setShortcut(config_scuts["window_browser find duplicates"])
    f.actionSelectNotes.setShortcut(config_scuts["window_browser select notes"])
    f.actionManage_Note_Types.setShortcut(config_scuts["window_browser manage note types"])




#detects shortcut conflicts
#Ignores the Add-on (Ω) options
def cs_conflictDetect():
    if config["Ω enable conflict warning"].upper() != "Y":
        return
    ext_list = {}
    dupes = False
    for e in config:
        sub = e[0:(e.find(" "))]
        val = config[e]
        if sub in ext_list:
            if isinstance(val,dict):
                for key in val:
                    ext_list[sub][key + " in " + e] = val[key].upper()
            else:
                ext_list[sub][e] = val.upper()
        elif sub != "Ω":
            ext_list[sub] = {e:val.upper()}
    inv = {}
    conflictStr = CS_CONFLICTSTR
    conflict = False
    for key in ext_list:
        inv = {}
        x = ext_list[key]
        for e in x:
            if x[e] not in inv:
                inv[x[e]] = [e]
            else:
                inv[x[e]].append(e)
        for k in inv:
            if(len(inv[k])) == 1:
                continue
            if k == "<NOP>":
                continue
            if not k:
                continue
            conflict = True
            conflictStr += ", ".join(inv[k])
            conflictStr += "\nshare '" + k + "' as a shortcut\n\n"
    if conflict:
        conflictStr += "\nThese shortcuts will not work.\n"
        conflictStr += "Please change them in the config.json."
        showWarning(conflictStr)

def cs_toolbarCenterLinks(self) -> str:
    links = [
        self.create_link(
            "decks",
            _("Decks"),
            self._deckLinkHandler,
            tip=_("Shortcut key: %s") % config_scuts["main deckbrowser"],
            id="decks",
        ),
        self.create_link(
            "add",
            _("Add"),
            self._addLinkHandler,
            tip=_("Shortcut key: %s") % config_scuts["main add"],
            id="add",
        ),
        self.create_link(
            "browse",
            _("Browse"),
            self._browseLinkHandler,
            tip=_("Shortcut key: %s") % config_scuts["main browse"],
            id="browse",
        ),
        self.create_link(
            "stats",
            _("Stats"),
            self._statsLinkHandler,
            tip=_("Shortcut key: %s") % config_scuts["main stats"],
            id="stats",
        ),
    ]

    links.append(self._create_sync_link())

    gui_hooks.top_toolbar_did_init_links(links, self)

    return "\n".join(links)

#Functions that execute on startup
Editor.customPaste = functions.cs_editor_custom_paste
Editor._customPaste = functions.cs_uEditor_custom_paste
Editor.onAltCloze = functions.cs_editor_onAltCloze
Editor._onAltCloze = functions.cs_uEditor_onAltCloze
Reviewer.sToF = functions.review_sToF
Editor.setupShortcuts = cs_editor_setupShortcuts
Reviewer._shortcutKeys = cs_review_setupShortcuts
Toolbar._centerLinks = cs_toolbarCenterLinks


#Shortcut setup for main window & other startup functions
cs_mt_setupShortcuts()
cs_main_setupShortcuts()
cs_conflictDetect()

#Redraws the toolbar with the new shortcuts
mw.toolbar.draw()

#Hooks to setup shortcuts at the right time
addHook('browser.setupMenus', cs_browser_setupShortcuts)


########################################################################
#SECTION 5
#This code shows the answer when you press the shortcuts for again, hard, good or easy.
#By default, Anki's code won't flip the card when you press those shortcuts--it would just go to the next card
#This solution was written entirely by Joseph. Yay.
#I tried to use the method of saving the original code and calling a custom version, as mentioned monkey patching section of the Anki 2.1 addon creation documentation
#But the code wouldn't work. So if something breaks with the addon in future Anki versions, look here and in section 2.
########################################################################

from aqt.reviewer import Reviewer

def _answerCardADDON(self, ease):
        "Call custom function for compatibility with ColorConfirmation add-on. Solution by MacMarc."
        try:
                self.CustomAnswerCard(ease)
        except Exception as e:
                pass
        "Reschedule card and show next."
        if self.mw.state != "review":
            # showing resetRequired screen; ignore key
            return
        if self.mw.col.sched.answerButtons(self.card) < ease:
            return
        if self.state == "question":
                self._getTypedAnswer()
        if self.state == "answer":
                self.mw.col.sched.answerCard(self.card, ease)
                self._answeredIds.append(self.card.id)
                self.mw.autosave()
                self.nextCard()

Reviewer._answerCard = _answerCardADDON
