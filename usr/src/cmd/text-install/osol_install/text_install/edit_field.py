
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# You can obtain a copy of the license at usr/src/OPENSOLARIS.LICENSE
# or http://www.opensolaris.org/os/licensing.
# See the License for the specific language governing permissions
# and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at usr/src/OPENSOLARIS.LICENSE.
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#
# Copyright (c) 2009, 2010, Oracle and/or its affiliates. All rights reserved.
#

'''
Support for building and utilizing an editable text field
'''

import logging
import curses
from curses.textpad import Textbox
from curses.ascii import isprint, ctrl, ismeta

from osol_install.text_install import LOG_LEVEL_INPUT
from osol_install.text_install.base_screen import UIMessage
from osol_install.text_install.scroll_window import ScrollWindow
from osol_install.text_install.i18n import rjust_columns
from osol_install.text_install.inner_window import consume_action, no_action
from osol_install.text_install.i18n import textwidth, charwidth


class EditField(ScrollWindow):
    '''EditFields represent editable text areas on the screen
    
    At any time, the text of the object can be accessed by
    referencing an EditField's 'text' parameter (edit_field.text).
    Note that this returns a list of character codes. To get a string,
    see EditField.get_text()
    
    '''
    
    ASTERISK_CHAR = ord('*')
    LARROW_CHAR = ord('<')
    
    CMD_DONE_EDIT = ord(ctrl('g'))
    CMD_MV_BOL = ord(ctrl('a')) # Move to beginning of line
    CMD_MV_EOL = ord(ctrl('e')) # Move to end of line
    CMD_CLR_LINE = ord(ctrl('k'))
    
    def __init__(self, area, window=None, text="", masked=False,
                 color_theme=None, color=None, highlight_color=None,
                 validate=None, on_exit=None, error_win=None,
                 numeric_pad=None, **kwargs):
        '''See InnerWindow.__init__
        
        In general, specifying a specific color_theme is unnecessary, unless
        this instance requires a theme other than that of the rest of the
        program 
        
        window (required): A parent InnerWindow
        
        area (required): Describes the area within the parent window to be used.
                         area.lines must be 1, as only single line EditFields
                         are currently supported.
        
        text (optional): The text in this field, before it is edited by
        the user. Defaults to empty string.
        
        masked (optional): If True, then this field will display bullets when
        the user types into it, instead of echo'ing the text
        
        color_theme (optional): The color_theme for this edit field. By default
        the parent window's theme is used. color_theme.edit_field is used
        as the background color; color_theme.highlight_edit is the background
        when this EditField is active.
        
        validate (optional) - A function for validation on each keystroke.
        The function passed in should take as parameter a string, and if
        invalid, it should raise a UIMessage with an indicator of why. This
        function, if present, will be called after each keystroke.
        IMPORTANT: If no UIMessage is raised, the string is assumed to be
        valid
        
        Additional keyword arguments can be passed to this function by
        modifying this EditField's validate_kwargs dictionary
        
        on_exit (optional) - A function for final validation. This is called
        when this EditField loses focus. Like validate, it should accept a
        string argument and raise a UIMessage if the string is not valid.
        
        Additional keyword arguments can be passed to this function by
        modifying this EditField's on_exit_kwargs dictionary
        
        error_win (optional) - If given, error_win.display_error() is called
        whenever validate or on_exit raise a UIMessage (the UIMessage's
        explanation string is passed as parameter). Additionally,
        error_win.clear_err() is called when those functions return
        successfully.
        
        numeric_pad (optional) - A single character to pad self.text with.
        If given, when this EditField handles input, it works in numeric mode.
        In numeric mode:
            * When editing begins, numeric_pad is stripped from the current
              text in the field. Text is shifted to the left to compensate
            * When done editing, the text is right justified, and padded with
              the value of numeric_pad. In general, either a space or zero will
              be used as the value of numeric_pad
            * IMPORTANT: The function hooks for 'validate' and 'on_exit' are
              called using the value of self.get_text PRIOR to padding.
        
        '''
        self.numeric_pad = numeric_pad
        self.right_justify = False
        self.on_exit_kwargs = {}
        self.validate_kwargs = {}
        self.validate = validate
        self.on_exit = on_exit
        self.error_win = error_win
        if color_theme is None:
            color_theme = window.color_theme
        if color is None:
            color = color_theme.edit_field
        if highlight_color is None:
            highlight_color = color_theme.highlight_edit
        
        if area.lines != 1:
            raise ValueError("area.lines must be 1")
        super(EditField, self).__init__(area, window=window,
                                        color_theme=color_theme, color=color,
                                        highlight_color=highlight_color,
                                        **kwargs)
        self.masked = masked
        self.masked_char = EditField.ASTERISK_CHAR
        self.textbox = Textbox(self.window)
        self.textbox.stripspaces = True
        self.input_key = None
        self.text = None
        self.key_dict[curses.KEY_ENTER] = consume_action
        self.key_dict[curses.KEY_LEFT] = no_action
        self.key_dict[curses.KEY_RIGHT] = no_action

        # Set use_horiz_scroll_bar to False to let edit_field handle
        # the drawing of the horiz scroll arrow, since it is inline with
        # the text. Do this before calling set_text, which does a screen
        # update and use_horiz_scroll_bar needs to be False by then. 
        self.use_horiz_scroll_bar = False
        self.set_text(text)
        self.clear_on_enter = False
    
    def set_text(self, text):
        '''Set the text of this EditField to text. Processes each
        character individually; thus emulating a user typing in the text.
        This means that each substring of text that start at text[0] must
        be valid in the context of any validation function this EditField
        has.
        
        If numeric_pad is set, pad text with it if field isn't blank.
        '''
        if self.numeric_pad is not None:
            width = self.area.columns - 1
            if text:
                text = text.lstrip(self.numeric_pad)
                text = rjust_columns(text, width, self.numeric_pad)
        self._set_text(text)
    
    def _set_text(self, text):
        '''Used internally to bypass the the public
        interface's numeric_pad functionality'''
        if text is None:
            text = ""
        self.clear_text()
        logging.log(LOG_LEVEL_INPUT,
                    "_set_text textwidth=%s, columns=%s, text=%s",
                    textwidth(text), self.area.columns, text)
        length_diff = textwidth(text) - self.area.columns 
        if (length_diff > 0):
            self.scroll(columns=length_diff)
        for idx, char in enumerate(text):
            if length_diff  > 0 and idx == length_diff:
                self.textbox.do_command(EditField.LARROW_CHAR)
            elif self.masked:
                self.textbox.do_command(self.masked_char)
            else:
                self.textbox.do_command(ord(char))
            self.text.append(char)
        self.no_ut_refresh()
    
    def handle_input(self, input_key):
        '''
        For each keystroke, determine if it's a special character (and needs
        to end editing), printable character, or backspace.
        
        For special characters, send the return the done-editing code (CTRL-G),
        and store the special character for processing by parent window
        objects.
        
        If printable, append it to self.text, and try to validate. If
        validation fails, reject the character.
        
        '''
        input_key = self.translate_input(input_key)
        if self.is_special_char(input_key):
            self.input_key = input_key
            return EditField.CMD_DONE_EDIT
        else:
            self.input_key = None
        if isprint(input_key) or (ismeta(input_key) and
                                  input_key < curses.KEY_MIN):
            # isprint: ASCII characters
            # ismeta and < curses.KEY_MIN: Remaining UTF-8 characters
            # > curses.KEY_MIN: Special key such as down arrow, backspace, etc.
            self.text.append(chr(input_key))
            if not self.is_valid():
                if len(self.text) > 0:
                    self.text.pop()
                return None
            if self.masked:
                input_key = self.masked_char
        elif input_key == curses.KEY_BACKSPACE:
            if len(self.text) > 0:
                del_char = self.text.pop()
                del_width = charwidth(del_char) 
                if textwidth(self.get_text()) >= self.area.columns:
                    self.scroll(columns=-del_width)
            self.is_valid()
            # Run self.is_valid here so that any functional side effects can
            # occur, but don't check the return value (removing a character
            # from a valid string should never be invalid, and even if it were,
            # it would not make sense to add the deleted character back in)

        return input_key
    
    def edit_loop(self):
        '''Loop for handling characters in an edit field.
        Called by EditField.process().
        
        '''
        input_key = None
        while input_key != EditField.CMD_DONE_EDIT:
            input_key = self.handle_input(self.getch())
            self.set_text(self.get_text())
            curses.doupdate()
    
    def process(self, input_key):
        '''Process a keystroke. For an EditField, this means preparing the
        textpad for processing and passing the input_key in.
        
        Try to enable the blinking cursor (if it was disabled) before
        editing begins, so the user can see where they're typing. Once
        finished, restore the cursor state to its previous condition.
        
        After editing, return self.input_key, which will either be None
        (indicating all keystrokes were processed by the Textbox) or
        a special character (such as F2) which caused EditField.handle_input
        to stop processing text through the Textbox.
        
        '''
        try:
            curses.curs_set(2)
        except curses.error:
            logging.debug("Got curses.error when enabling cursor")
        
        if input_key is not None and not self.is_special_char(input_key):
            # Put input_key back on stack so that textbox.edit can read it
            curses.ungetch(input_key)
            if self.numeric_pad is not None:
                self._set_text(self.get_text().lstrip(self.numeric_pad))
            
            if self.clear_on_enter:
                self.clear_text()
            else:
                # Move to end of previous input.
                self.textbox.do_command(EditField.CMD_MV_EOL)
            self.edit_loop()
            return_key = self.input_key
            if self.numeric_pad is not None:
                self.set_text(self.get_text())
        else:
            return_key = input_key
        logging.debug("Returning: %s", return_key)
        return return_key
    
    def get_text(self):
        '''Join the array of characters as a unicode string'''
        return "".join(self.text)
    
    def is_special_char(self, input_key):
        '''Check to see if this is a keystroke that should break us out of
        adding input to the Textbox and return control to the parent window
        
        '''
        if (input_key in range(curses.KEY_F0, curses.KEY_F10) or
            input_key in self.key_dict):
            return True
        else:
            return False
    
    def is_valid(self):
        '''Check to see if the text we have is valid or not.
        First check the length to make sure it fits in the space alloted.
        If it doesn't, flag an error indicating the maximum supported 
        length for the field.

        Then, if this EditField has a validate function, call it (passing
        in any validate_kwargs we have).
        
        If validate raises an exception, display the error (if we have a
        handle to an ErrorWindow) and return False.
        
        '''
        win_size_x = self.window.getmaxyx()[1]
        if len(self.get_text().lstrip(self.numeric_pad)) >= win_size_x:
            if self.error_win is not None:
                self.error_win.display_err("Max supported field length: %s"
                    % (win_size_x - 1))
            return False
        elif callable(self.validate):
            try:
                self.validate(self, **self.validate_kwargs)
            except UIMessage as error_str:
                if self.error_win is not None:
                    self.error_win.display_err(str(error_str))
                return False
        if self.error_win is not None and self.error_win.visible:
            self.error_win.clear_err()
        return True
    
    def run_on_exit(self):
        '''Fire the on_exit function, if there is one. If an error occurs,
        and this EditField has an error_win, display it there.
        
        '''
        if callable(self.on_exit):
            try:
                self.on_exit(self, **self.on_exit_kwargs)
                if self.error_win is not None and self.error_win.visible:
                    self.error_win.clear_err()
                return True
            except UIMessage as error_str:
                if self.error_win is not None:
                    self.error_win.display_err(str(error_str))
                return False
        return True
    
    def make_active(self):
        '''Enable the cursor when activating this field'''
        super(EditField, self).make_active()
        try:
            curses.curs_set(2)
        except curses.error:
            logging.debug("Got curses.error when enabling cursor")
    
    def make_inactive(self):
        '''Fire the on_exit function before leaving the field and making
        it inactive.
        
        '''
        self.run_on_exit()
        try:
            curses.curs_set(0)
        except curses.error:
            logging.debug("Got curses.error when reverting cursor")
        super(EditField, self).make_inactive()
    
    def clear_text(self):
        '''Issue the commands to textbox to clear itself, reset self.text
        to an empty array, and reset horizontal scrolling. 
        
        '''
        # Move cursor to left side of window
        self.textbox.do_command(EditField.CMD_MV_BOL)
        # Clear from cursor to end of line
        self.textbox.do_command(EditField.CMD_CLR_LINE)
        self.text = []
        self.scroll(scroll_to_column=0)
        self.no_ut_refresh()
    
    def get_cursor_loc(self):
        '''Cursor should be positioned at the end of the entered text'''
        win_loc = self.window.getbegyx()
        x_loc = win_loc[1]
        if not self.clear_on_enter:
            x_loc += min(textwidth(self.get_text()), self.area.columns)
        return (win_loc[0], x_loc)
