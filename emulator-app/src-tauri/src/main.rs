#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod app_menu;
mod native_buttons;
mod tenv;

use tauri::Manager;
use window_vibrancy::{
    apply_liquid_glass, apply_vibrancy, LiquidGlassOptions, NSGlassEffectViewStyle,
    NSVisualEffectMaterial, NSVisualEffectState,
};

#[tauri::command]
fn quit(app: tauri::AppHandle) {
    app.exit(0);
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            quit,
            native_buttons::native_buttons_available,
            native_buttons::layout_native_buttons,
            app_menu::update_menu,
            tenv::start_tenv
        ])
        .setup(|app| {
            let window = app.get_webview_window("main").unwrap();

            #[cfg(target_os = "macos")]
            if apply_liquid_glass(&window, LiquidGlassOptions::new(NSGlassEffectViewStyle::Regular))
                .is_ok()
            {
                native_buttons::install(app.handle(), window.ns_view()?);
            } else {
                apply_vibrancy(
                    &window,
                    NSVisualEffectMaterial::HudWindow,
                    Some(NSVisualEffectState::Active),
                    None,
                )
                .expect("Failed to apply vibrancy");
            }

            app.set_menu(app_menu::initial(app.handle())?)?;

            Ok(())
        })
        .on_menu_event(|app, event| app_menu::forward_event(app, event.id().as_ref()))
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
