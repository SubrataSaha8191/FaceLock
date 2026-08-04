pragma Singleton
import QtQuick

QtObject {
    // ── Pure Flat Dark System — Editorial / Scrib3 / Noomo Style ──
    readonly property color background: "#0A0A0A"
    readonly property color surfaceRaised: "#141414"
    readonly property color surfaceBorder: "#1E1E1E"
    readonly property color divider: "#1E1E1E"

    // ── Backward-compat tokens used by subpages ──
    readonly property color glassCard: "#141414"
    readonly property color glassBorder: "#1E1E1E"
    readonly property color glassBorderHover: "#FFFFFF"
    readonly property color cardBackground: "#141414"
    readonly property color cardHover: "#1A1A1A"

    // ── Typography Palette ──
    readonly property color textPrimary: "#FFFFFF"
    readonly property color textSecondary: "#888888"
    readonly property color textMuted: "#555555"

    // ── Accent — Single Restrained Cyan ──
    readonly property color accent: "#FFFFFF"
    readonly property color accentGlow: "#1E1E1E"
    readonly property color primary: "#FFFFFF"
    readonly property color primaryText: "#0A0A0A"
    readonly property color success: "#4ADE80"
    readonly property color danger: "#F87171"

    // ── Font Sizes ──
    readonly property int fontSizeXs: 10
    readonly property int fontSizeSmall: 12
    readonly property int fontSizeBody: 14
    readonly property int fontSizeTitle: 18
    readonly property int fontSizeHeader: 24
    readonly property int fontSizeHero: 42

    // ── Radii — Minimal ──
    readonly property real cornerRadius: 4.0
    readonly property real cornerRadiusSmall: 3.0

    // ── Transitions ──
    readonly property int animFast: 100
    readonly property int animNormal: 200
}
