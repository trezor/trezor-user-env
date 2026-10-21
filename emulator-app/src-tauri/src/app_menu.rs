//! macOS menu bar mirroring the in-window controls.
//! JS pushes its state via `update_menu`; clicks come back as `menu-action` events with the item id.

use serde::Deserialize;
use tauri::menu::{CheckMenuItemBuilder, Menu, MenuBuilder, MenuItemBuilder, SubmenuBuilder};
use tauri::{AppHandle, Emitter, Runtime};

#[derive(Deserialize, Default)]
#[serde(rename_all = "camelCase")]
pub struct MenuState {
    models: Vec<ModelEntry>,
    model: String,
    versions: Vec<String>,
    version: String,
    wipe: bool,
    seed_on_start: bool,
    always_on_top: bool,
    running: bool,
    connected: bool,
    tenv_starting: bool,
    bridge_running: bool,
    bridge_pending: bool,
    drawer_open: bool,
}

#[derive(Deserialize)]
pub struct ModelEntry {
    id: String,
    name: String,
}

const DEVICE_COMMANDS: &[(&str, &str, Option<&str>)] = &[
    ("cmd:yes", "Confirm", Some("CmdOrCtrl+Enter")),
    ("cmd:no", "Cancel", Some("CmdOrCtrl+Backspace")),
    ("-", "", None),
    ("cmd:seed-all", "Load Seed \u{201c}all\u{201d} (12 words)", None),
    ("cmd:seed-academic", "Load Seed \u{201c}academic\u{201d} (20 words)", None),
    ("cmd:confirm-mnemonic", "Read & Confirm Mnemonic", None),
    ("-", "", None),
    ("cmd:features", "Get Features", None),
    ("cmd:unsafe", "Turn Off Safety Checks", None),
    ("-", "", None),
    ("cmd:reset", "Reset Device", None),
    ("cmd:wipe", "Wipe Device", None),
];

pub fn build<R: Runtime>(app: &AppHandle<R>, s: &MenuState) -> tauri::Result<Menu<R>> {
    let app_menu = SubmenuBuilder::new(app, "Trezor User Env")
        .about(None)
        .separator()
        .hide()
        .hide_others()
        .show_all()
        .separator()
        .quit()
        .build()?;

    let edit_menu = SubmenuBuilder::new(app, "Edit")
        .copy()
        .paste()
        .select_all()
        .build()?;

    let mut model_menu = SubmenuBuilder::new(app, "Model");
    for (i, m) in s.models.iter().enumerate() {
        let mut item = CheckMenuItemBuilder::with_id(format!("model:{}", m.id), format!("{} \u{2014} {}", m.id, m.name))
            .checked(m.id == s.model);
        if i < 9 {
            item = item.accelerator(format!("CmdOrCtrl+{}", i + 1));
        }
        model_menu = model_menu.item(&item.build(app)?);
    }

    let mut version_menu = SubmenuBuilder::new(app, "Firmware Version");
    if s.versions.is_empty() {
        version_menu = version_menu.item(
            &MenuItemBuilder::with_id("version:none", "No Versions Available")
                .enabled(false)
                .build(app)?,
        );
    }
    for v in &s.versions {
        version_menu = version_menu.item(
            &CheckMenuItemBuilder::with_id(format!("version:{v}"), v)
                .checked(*v == s.version)
                .build(app)?,
        );
    }

    let emulator_menu = SubmenuBuilder::new(app, "Emulator")
        .item(
            &MenuItemBuilder::with_id("start-tenv", "Start trezor-user-env")
                .enabled(!s.connected && !s.tenv_starting)
                .build(app)?,
        )
        .separator()
        .item(
            &MenuItemBuilder::with_id("start", "Start")
                .accelerator("CmdOrCtrl+R")
                .enabled(s.connected && !s.versions.is_empty())
                .build(app)?,
        )
        .item(
            &MenuItemBuilder::with_id("stop", "Stop")
                .accelerator("CmdOrCtrl+.")
                .enabled(s.connected && s.running)
                .build(app)?,
        )
        .separator()
        .item(&model_menu.build()?)
        .item(&version_menu.build()?)
        .item(
            &CheckMenuItemBuilder::with_id("wipe-on-start", "Wipe on Start")
                .checked(s.wipe)
                .build(app)?,
        )
        .item(
            &CheckMenuItemBuilder::with_id("seed-on-start", "Load Seed \u{201c}all\u{201d} on Start")
                .checked(s.seed_on_start)
                .build(app)?,
        )
        .separator()
        .item(
            &MenuItemBuilder::with_id(
                "toggle-bridge",
                if s.bridge_running { "Stop Bridge" } else { "Start Bridge" },
            )
            .accelerator("CmdOrCtrl+B")
            .enabled(s.connected && !s.bridge_pending)
            .build(app)?,
        )
        .build()?;

    let device_enabled = s.connected && s.running;
    let mut device_menu = SubmenuBuilder::new(app, "Device");
    for (id, label, accel) in DEVICE_COMMANDS {
        if *id == "-" {
            device_menu = device_menu.separator();
            continue;
        }
        let mut item = MenuItemBuilder::with_id(*id, *label).enabled(device_enabled);
        if let Some(accel) = accel {
            item = item.accelerator(accel);
        }
        device_menu = device_menu.item(&item.build(app)?);
    }

    let view_menu = SubmenuBuilder::new(app, "View")
        .item(
            &CheckMenuItemBuilder::with_id("toggle-commands", "Show Commands")
                .accelerator("CmdOrCtrl+J")
                .checked(s.drawer_open)
                .build(app)?,
        )
        .item(
            &CheckMenuItemBuilder::with_id("always-on-top", "Always on Top")
                .checked(s.always_on_top)
                .build(app)?,
        )
        .build()?;

    MenuBuilder::new(app)
        .item(&app_menu)
        .item(&edit_menu)
        .item(&emulator_menu)
        .item(&device_menu.build()?)
        .item(&view_menu)
        .build()
}

pub fn initial<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<Menu<R>> {
    build(app, &MenuState::default())
}

pub fn forward_event<R: Runtime>(app: &AppHandle<R>, id: &str) {
    let _ = app.emit("menu-action", id);
}

#[tauri::command]
pub fn update_menu(app: AppHandle, state: MenuState) -> Result<(), String> {
    let menu = build(&app, &state).map_err(|e| e.to_string())?;
    app.set_menu(menu).map_err(|e| e.to_string())?;
    Ok(())
}
