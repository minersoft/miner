from __future__ import print_function, unicode_literals, absolute_import

class baseconsole(object):
    def __init__(self):
        pass
        
    def bell(self):
        raise NotImplementedError

    def pos(self, x=None, y=None):
        '''Move or query the window cursor.'''
        raise NotImplementedError

    def size(self):
        raise NotImplementedError

    def rectangle(self, rect, attr=None, fill=' '):
        '''Fill Rectangle.'''
        raise NotImplementedError

    def write_scrolling(self, text, attr=None):
        '''write text at current cursor position while watching for scrolling.

        If the window scrolls because you are at the bottom of the screen
        buffer, all positions that you are storing will be shifted by the
        scroll amount. For example, I remember the cursor position of the
        prompt so that I can redraw the line but if the window scrolls,
        the remembered position is off.

        This variant of write tries to keep track of the cursor position
        so that it will know when the screen buffer is scrolled. It
        returns the number of lines that the buffer scrolled.

        '''
        raise NotImplementedError
    
    def getkeypress(self):
        '''Return next key press event from the queue, ignoring others.'''
        raise NotImplementedError
        
    def write(self, text):
        raise NotImplementedError
    
    def page(self, attr=None, fill=' '):
        '''Fill the entire screen.'''
        raise NotImplementedError

    def isatty(self):
        return True

    def flush(self):
        pass

    def clear_range(self, pos_range):
        '''Clears range that may span to multiple lines
        pas_range is (x1,y1, x2,y2) including
        y2 >= y1
        x2 == -1 mean end of line
        Child classes may provide more efficient implementation
        '''
        w, h = self.size()
        (x1,y1, x2,y2) = pos_range
        if x2 < 0:
            x2 = w - 1
        if y2 < y1:
            return
        elif y2 == y1:
            self.rectangle((x1, y1, x2+1, y2+1))
            return
        else:
            full_rec = [0,y1, w, y2+1]
            if x1 > 0:
                self.rectangle((x1,y1, w, y1+1))
                full_rec[1] = y1+1
            if x2 < w-1:
                self.rectangle((0,y2, x2+1, y2+1))
                full_rec[3] = y2
            if full_rec[1] < full_rec[3]:
                self.rectangle(tuple(full_rec))

    def more_events_pending(self):
        '''This is performance optimization function.
        If specific console implementation is able to say that there are more keys
        present in the queue then they can be processed at once before screen is
        updated.
        '''
        return False

    def get_default_selection_attr(self):
        '''This function returns default representation attributes for selected text.
        Default implementation sets background  color to saved foreground color and sets
        foreground to 0.
        Although in some implementation when initial color scheme is unknown this is not good
        solution
        '''
        return self.saveattr<<4
    
    def clear_state(self):
        '''Clears internal caches of console object'''
        pass
