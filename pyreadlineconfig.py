show_all_if_ambiguous("on")
mark_directories("on")
completer_delims(" \t\n\"\\'`~@$><=,;:^!|&{}()[]?+-*/%")
#complete_filesystem("on")
debug_output("off")
#allow_ctrl_c(True)  #(Allows use of ctrl-c as copy key, still propagate keyboardinterrupt when not waiting for input)

history_filename("~/.coalhistory")
history_length(1000) #value of -1 means no limit

def get_miner_command(mode):
    l = mode.l_buffer
    bufLen = len(l.line_buffer)
    start = l.point
    
    if start >= bufLen:
        start = bufLen-1
    while (start >= 0):
        if l.line_buffer[start] == '|':
            break
        start -= 1
    start += 1
    while start < bufLen and l.line_buffer[start].isspace():
        start += 1
    end = start
    while end < bufLen and l.line_buffer[end].isalpha():
        end+=1
    return ''.join(l.line_buffer[start:end])


def miner_command_help(self, e):
    """Prints help on miner command"""
    import pyreadline.lineeditor.lineobj
    from m.executor import printHelp
    l = self.l_buffer
    self.go_end_of_line()
    self.console.write('\n\n')
    #text = self.get_current_completed_word()
    text = get_miner_command(self)
    if not text:
        print("No Id selected")
    else:
        printHelp(text)
    self.console.write('\n')
    self._print_prompt()
    self.finalize()

bind_key("F1", miner_command_help)

def python_documentation(self, e):
    """Prints documentation on current python object"""
    import pyreadline.lineeditor.lineobj
    from m.executor import printDoc
    l = self.l_buffer
    self.go_end_of_line()
    self.console.write('\n\n')
    text = self.get_current_completed_word()
    if not text:
        print("No Id selected")
    else:
        printDoc(text)
    self.console.write('\n')
    self._print_prompt()
    self.finalize()

bind_key("F2", python_documentation)

def moveToPipe(editmode, direction):
    import pyreadline.lineeditor.lineobj
    l = editmode.l_buffer.line_buffer
    
    size = len(l)
    if size==0:
        return
    pos = editmode.l_buffer.point
    newPos = pos
    #print("newPos=%d size=%d dir=%d" % (newPos, size, direction))
    if newPos >= size:
        if direction > 0:
            return
        else:
            newPos += direction
    elif l[newPos] == '|':
        newPos += direction
    if direction < 0:
        while newPos > 0:
            if l[newPos] == '|':
                break
            newPos += direction
    else:
        while newPos < size:
            if l[newPos] == '|':
                break
            newPos += direction
    editmode.l_buffer.point = newPos
    w,h = editmode.console.size()
    x,y = editmode.console.pos()
    newAbs = x + y*w + (newPos - pos)*direction
    newY = newAbs/w
    newX = newAbs%w
    editmode.console.pos(newX, newY)

def move_prev_command(self, e):
    """Goes to the previous miner chain command"""
    moveToPipe(self, -1)

def move_next_command(self, e):
    """Goes to the next miner chain command"""
    moveToPipe(self, 1)

def deleteToPipe(editmode, direction):
    import pyreadline.lineeditor.lineobj
    l = editmode.l_buffer.line_buffer
    
    size = len(l)
    if size==0:
        return
    pos = editmode.l_buffer.point
    newPos = pos
    if newPos >= size:
        if direction > 0:
            return
        else:
            newPos += direction
    if l[newPos] == '|':
        if direction > 0:
            newPos += 1
        else:
            newPos = pos -1
        
    if direction < 0:
        while newPos > 0:
            if l[newPos] == '|':
                break
            newPos += direction
        editmode.l_buffer.backward_delete_char(pos - newPos)
    else:
        while newPos < size:
            if l[newPos] == '|':
                break
            newPos += direction
            #editmode.l_buffer.delete_char()
        editmode.l_buffer.delete_char(newPos - pos)
    editmode.finalize()

def backward_delete_to_pipe(self, e):
    deleteToPipe(self, -1)
def forward_delete_to_pipe(self, e):
    deleteToPipe(self, 1)

def insertLast(editmode, history, isSource):
    historyCursor = history.get_history_cursor()
    if historyCursor == 0:
        return
    text = history.get_history_item(historyCursor)
    if isSource:
        pipePos = text.find("|")
        if pipePos < 0:
            return
        editmode.insert_text(text[:pipePos])
    else:
        pipePos = text.rfind("|")
        if pipePos < 0:
            return
        editmode.insert_text(text[pipePos:])
    editmode.finalize()

def insert_last_source(self, e):
    insertLast(self, self._history, isSource=True)
def insert_last_destination(self, e):
    insertLast(self, self._history, isSource=False)

def show_bindings(self, e):
    from pyreadline.keysyms.common import KeyPress
    self.go_end_of_line()
    self.console.write('\n\n')
    print("------------- key bindings ------------")
    tablepat=u"%-7s %-7s %-7s %-15s %-15s "
    for k,v in sorted(self.key_dispatch.iteritems()):
        print("%-17s %s" % (str(KeyPress(control=k[0], meta=k[1], shift=k[2], keyname=k[3])), v.__name__.replace("_", " ")))
    self._print_prompt()
    self.finalize()

from pyreadline.modes.emacs import EmacsMode

bind_key("alt-left", move_prev_command)
bind_key("alt-right", move_next_command)
bind_key("ctrl-shift-left", move_prev_command)
bind_key("ctrl-shift-right", move_next_command)

bind_key("up", EmacsMode.previous_history)
bind_key("down", EmacsMode.next_history)

bind_key('ctrl-b', EmacsMode.history_search_backward)
bind_key('ctrl-f', EmacsMode.history_search_forward)

bind_key("ctrl-k", show_bindings)
bind_key("alt-backspace", backward_delete_to_pipe)
bind_key("ctrl-delete", backward_delete_to_pipe)
bind_key("alt-delete", forward_delete_to_pipe)
bind_key("ctrl-shift-delete", forward_delete_to_pipe)
bind_key("alt-,", insert_last_source)
bind_key("alt-<", insert_last_source)
bind_key("alt-.", insert_last_destination)
bind_key("alt->", insert_last_destination)
    

