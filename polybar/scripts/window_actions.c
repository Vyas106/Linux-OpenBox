#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <X11/Xlib.h>
#include <X11/Xatom.h>
#include <X11/Xutil.h>

#define IconicState 3
#define NormalState 1

static int is_desktop_or_dock(Display *d, Window w) {
    Atom net_wm_type = XInternAtom(d, "_NET_WM_WINDOW_TYPE", False);
    Atom type_dock = XInternAtom(d, "_NET_WM_WINDOW_TYPE_DOCK", False);
    Atom type_desktop = XInternAtom(d, "_NET_WM_WINDOW_TYPE_DESKTOP", False);
    Atom atom_type = XInternAtom(d, "ATOM", False);
    
    Atom actual_type;
    int actual_format;
    unsigned long nitems, bytes_after;
    unsigned char *prop = NULL;
    
    int is_special = 0;
    if (XGetWindowProperty(d, w, net_wm_type, 0, 32, False, atom_type,
                           &actual_type, &actual_format, &nitems, &bytes_after, &prop) == Success) {
        if (prop && nitems > 0) {
            Atom *types = (Atom *)prop;
            for (unsigned long i = 0; i < nitems; i++) {
                if (types[i] == type_dock || types[i] == type_desktop) {
                    is_special = 1;
                    break;
                }
            }
        }
        if (prop) XFree(prop);
    }
    
    if (!is_special) {
        XClassHint ch;
        if (XGetClassHint(d, w, &ch)) {
            if (ch.res_name) {
                if (strcasecmp(ch.res_name, "conky") == 0 || strcasecmp(ch.res_name, "polybar") == 0) {
                    is_special = 1;
                }
                XFree(ch.res_name);
            }
            if (ch.res_class) {
                if (strcasecmp(ch.res_class, "conky") == 0 || strcasecmp(ch.res_class, "polybar") == 0) {
                    is_special = 1;
                }
                XFree(ch.res_class);
            }
        }
    }
    return is_special;
}

static Window *get_client_windows(Display *d, Window root, unsigned long *count) {
    Atom net_client_list = XInternAtom(d, "_NET_CLIENT_LIST", False);
    Atom win_type = XInternAtom(d, "WINDOW", False);
    
    Atom actual_type;
    int actual_format;
    unsigned long nitems = 0, bytes_after;
    unsigned char *prop = NULL;
    
    if (XGetWindowProperty(d, root, net_client_list, 0, 4096, False, win_type,
                           &actual_type, &actual_format, &nitems, &bytes_after, &prop) == Success) {
        if (prop && nitems > 0) {
            Window *list = malloc(sizeof(Window) * nitems);
            memcpy(list, prop, sizeof(Window) * nitems);
            XFree(prop);
            *count = nitems;
            return list;
        }
        if (prop) XFree(prop);
    }
    *count = 0;
    return NULL;
}

static int get_window_state(Display *d, Window w) {
    Atom wm_state = XInternAtom(d, "WM_STATE", False);
    Atom actual_type;
    int actual_format;
    unsigned long nitems, bytes_after;
    unsigned char *prop = NULL;
    int state = NormalState;
    
    if (XGetWindowProperty(d, w, wm_state, 0, 2, False, wm_state,
                           &actual_type, &actual_format, &nitems, &bytes_after, &prop) == Success) {
        if (prop && nitems > 0) {
            state = (int)*((unsigned long *)prop);
        }
        if (prop) XFree(prop);
    }
    return state;
}

void toggle_minimize(Display *d, Window root) {
    unsigned long count = 0;
    Window *wins = get_client_windows(d, root, &count);
    if (!wins || count == 0) return;
    
    int screen = DefaultScreen(d);
    Atom wm_change_state = XInternAtom(d, "WM_CHANGE_STATE", False);
    Atom net_showing = XInternAtom(d, "_NET_SHOWING_DESKTOP", False);
    Atom net_active = XInternAtom(d, "_NET_ACTIVE_WINDOW", False);
    
    // Check if any normal window is not iconified
    int has_visible = 0;
    for (unsigned long i = 0; i < count; i++) {
        if (is_desktop_or_dock(d, wins[i])) continue;
        if (get_window_state(d, wins[i]) != IconicState) {
            has_visible = 1;
            break;
        }
    }
    
    if (has_visible) {
        // Minimize all windows
        for (unsigned long i = 0; i < count; i++) {
            if (is_desktop_or_dock(d, wins[i])) continue;
            
            // ICCCM WM_CHANGE_STATE
            XEvent ev;
            memset(&ev, 0, sizeof(ev));
            ev.type = ClientMessage;
            ev.xclient.type = ClientMessage;
            ev.xclient.window = wins[i];
            ev.xclient.message_type = wm_change_state;
            ev.xclient.format = 32;
            ev.xclient.data.l[0] = IconicState;
            XSendEvent(d, root, False, SubstructureRedirectMask | SubstructureNotifyMask, &ev);
            
            // Direct Xlib iconify
            XIconifyWindow(d, wins[i], screen);
        }
        
        // EWMH showing desktop on
        XEvent ev_d;
        memset(&ev_d, 0, sizeof(ev_d));
        ev_d.type = ClientMessage;
        ev_d.xclient.type = ClientMessage;
        ev_d.xclient.window = root;
        ev_d.xclient.message_type = net_showing;
        ev_d.xclient.format = 32;
        ev_d.xclient.data.l[0] = 1;
        XSendEvent(d, root, False, SubstructureRedirectMask | SubstructureNotifyMask, &ev_d);
    } else {
        // Restore all windows
        for (unsigned long i = 0; i < count; i++) {
            if (is_desktop_or_dock(d, wins[i])) continue;
            
            XMapWindow(d, wins[i]);
            XRaiseWindow(d, wins[i]);
            
            XEvent ev;
            memset(&ev, 0, sizeof(ev));
            ev.type = ClientMessage;
            ev.xclient.type = ClientMessage;
            ev.xclient.window = wins[i];
            ev.xclient.message_type = net_active;
            ev.xclient.format = 32;
            ev.xclient.data.l[0] = 2;
            ev.xclient.data.l[1] = CurrentTime;
            XSendEvent(d, root, False, SubstructureRedirectMask | SubstructureNotifyMask, &ev);
        }
        
        // EWMH showing desktop off
        XEvent ev_d;
        memset(&ev_d, 0, sizeof(ev_d));
        ev_d.type = ClientMessage;
        ev_d.xclient.type = ClientMessage;
        ev_d.xclient.window = root;
        ev_d.xclient.message_type = net_showing;
        ev_d.xclient.format = 32;
        ev_d.xclient.data.l[0] = 0;
        XSendEvent(d, root, False, SubstructureRedirectMask | SubstructureNotifyMask, &ev_d);
    }
    
    XFlush(d);
    free(wins);
}

void close_all(Display *d, Window root) {
    unsigned long count = 0;
    Window *wins = get_client_windows(d, root, &count);
    if (!wins || count == 0) return;
    
    Atom wm_protocols = XInternAtom(d, "WM_PROTOCOLS", False);
    Atom wm_delete = XInternAtom(d, "WM_DELETE_WINDOW", False);
    Atom net_close = XInternAtom(d, "_NET_CLOSE_WINDOW", False);
    
    for (unsigned long i = 0; i < count; i++) {
        Window w = wins[i];
        if (is_desktop_or_dock(d, w)) continue;
        
        // 1. Send WM_DELETE_WINDOW
        XEvent ev1;
        memset(&ev1, 0, sizeof(ev1));
        ev1.type = ClientMessage;
        ev1.xclient.type = ClientMessage;
        ev1.xclient.window = w;
        ev1.xclient.message_type = wm_protocols;
        ev1.xclient.format = 32;
        ev1.xclient.data.l[0] = wm_delete;
        ev1.xclient.data.l[1] = CurrentTime;
        XSendEvent(d, w, False, NoEventMask, &ev1);
        
        // 2. Send _NET_CLOSE_WINDOW to root
        XEvent ev2;
        memset(&ev2, 0, sizeof(ev2));
        ev2.type = ClientMessage;
        ev2.xclient.type = ClientMessage;
        ev2.xclient.window = w;
        ev2.xclient.message_type = net_close;
        ev2.xclient.format = 32;
        ev2.xclient.data.l[0] = CurrentTime;
        ev2.xclient.data.l[1] = 2; // Source indicator
        XSendEvent(d, root, False, SubstructureRedirectMask | SubstructureNotifyMask, &ev2);
    }
    
    XFlush(d);
    free(wins);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s [minimize|close_all]\n", argv[0]);
        return 1;
    }
    
    Display *d = XOpenDisplay(NULL);
    if (!d) {
        fprintf(stderr, "Cannot open X display\n");
        return 1;
    }
    
    Window root = DefaultRootWindow(d);
    
    if (strcmp(argv[1], "minimize") == 0 || strcmp(argv[1], "minimize_all") == 0) {
        toggle_minimize(d, root);
    } else if (strcmp(argv[1], "close_all") == 0 || strcmp(argv[1], "close") == 0) {
        close_all(d, root);
    } else {
        fprintf(stderr, "Unknown command: %s\n", argv[1]);
    }
    
    XCloseDisplay(d);
    return 0;
}
