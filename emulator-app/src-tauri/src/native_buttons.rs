//! Native AppKit Liquid Glass buttons layered over the webview.
//! JS reports where the HTML placeholders are; clicks come back as `native-button` events.

use std::cell::RefCell;
use std::ffi::c_void;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::OnceLock;

use objc2::rc::Retained;
use objc2::runtime::{AnyObject, NSObject};
use objc2::{define_class, msg_send, sel, MainThreadMarker, MainThreadOnly};
use objc2_app_kit::{
    NSBezelStyle, NSButton, NSCellImagePosition, NSColor, NSControlBorderShape, NSControlSize,
    NSImage, NSTintProminence, NSView,
};
use objc2_foundation::{NSObjectProtocol, NSPoint, NSRect, NSSize, NSString};
use serde::Deserialize;
use tauri::{AppHandle, Emitter};

static APP: OnceLock<AppHandle> = OnceLock::new();
static INSTALLED: AtomicBool = AtomicBool::new(false);

define_class!(
    #[unsafe(super(NSObject))]
    #[thread_kind = MainThreadOnly]
    #[name = "TrezorEmulatorButtonTarget"]
    struct ButtonTarget;

    impl ButtonTarget {
        #[unsafe(method(clicked:))]
        fn clicked(&self, sender: &NSButton) {
            if let Some(app) = APP.get() {
                let _ = app.emit("native-button", sender.tag());
            }
        }
    }

    unsafe impl NSObjectProtocol for ButtonTarget {}
);

impl ButtonTarget {
    fn new(mtm: MainThreadMarker) -> Retained<Self> {
        let this = Self::alloc(mtm).set_ivars(());
        unsafe { msg_send![super(this), init] }
    }
}

struct State {
    root: Retained<NSView>,
    buttons: Vec<Retained<NSButton>>,
    _target: Retained<ButtonTarget>,
}

thread_local! {
    static STATE: RefCell<Option<State>> = const { RefCell::new(None) };
}

fn make_button(
    mtm: MainThreadMarker,
    target: &ButtonTarget,
    title: &str,
    symbol: &str,
    tag: isize,
) -> Retained<NSButton> {
    let target: &AnyObject = target;
    let button = unsafe {
        NSButton::buttonWithTitle_target_action(
            &NSString::from_str(title),
            Some(target),
            Some(sel!(clicked:)),
            mtm,
        )
    };
    button.setBezelStyle(NSBezelStyle::Glass);
    button.setBorderShape(NSControlBorderShape::Capsule);
    button.setControlSize(NSControlSize::Large);
    if let Some(image) =
        NSImage::imageWithSystemSymbolName_accessibilityDescription(&NSString::from_str(symbol), None)
    {
        button.setImage(Some(&image));
        button.setImagePosition(NSCellImagePosition::ImageLeading);
    }
    button.setTag(tag);
    button.setHidden(true);
    button
}

/// Must run on the main thread. `ns_view` is the window's content view.
pub fn install(app: &AppHandle, ns_view: *mut c_void) {
    let Some(mtm) = MainThreadMarker::new() else { return };
    let Some(root) = (unsafe { Retained::retain(ns_view.cast::<NSView>()) }) else { return };
    let _ = APP.set(app.clone());

    let target = ButtonTarget::new(mtm);

    let start = make_button(mtm, &target, "Start", "play.fill", 1);
    start.setTintProminence(NSTintProminence::Primary);
    start.setBezelColor(Some(&NSColor::systemGreenColor()));

    let stop = make_button(mtm, &target, "Stop", "stop.fill", 2);
    stop.setContentTintColor(Some(&NSColor::systemRedColor()));

    for button in [&start, &stop] {
        root.addSubview(button);
    }

    STATE.with(|s| {
        *s.borrow_mut() = Some(State { root, buttons: vec![start, stop], _target: target });
    });
    INSTALLED.store(true, Ordering::SeqCst);
}

#[tauri::command]
pub fn native_buttons_available() -> bool {
    INSTALLED.load(Ordering::SeqCst)
}

#[derive(Deserialize)]
pub struct ButtonRect {
    tag: isize,
    x: f64,
    y: f64,
    w: f64,
    h: f64,
    visible: bool,
}

#[tauri::command]
pub fn layout_native_buttons(app: AppHandle, rects: Vec<ButtonRect>) {
    let _ = app.run_on_main_thread(move || {
        STATE.with(|s| {
            let state = s.borrow();
            let Some(state) = state.as_ref() else { return };
            let bounds = state.root.bounds();
            let flipped = state.root.isFlipped();
            for r in &rects {
                let Some(button) = state.buttons.iter().find(|b| b.tag() == r.tag) else { continue };
                let y = if flipped { r.y } else { bounds.size.height - r.y - r.h };
                button.setFrame(NSRect::new(NSPoint::new(r.x, y), NSSize::new(r.w, r.h)));
                button.setHidden(!r.visible);
            }
        });
    });
}
