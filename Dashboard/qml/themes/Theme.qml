pragma Singleton
import QtQuick

QtObject {
    // ── Core Palette ──
    readonly property color background: "#0B0F19"
    readonly property color surface: "#111827"
    readonly property color surfaceElevated: "#1A2235"
    readonly property color surfaceBorder: "#1F2A40"
    readonly property color surfaceGlow: "#06B6D4"

    // ── Accent Colors ──
    readonly property color primary: "#06B6D4"
    readonly property color primaryHover: "#22D3EE"
    readonly property color primaryMuted: "#164E63"
    readonly property color gradientStart: "#06B6D4"
    readonly property color gradientEnd: "#8B5CF6"
    readonly property color success: "#10B981"
    readonly property color danger: "#F43F5E"
    readonly property color warning: "#F59E0B"
    readonly property color info: "#3B82F6"

    // ── Text Colors ──
    readonly property color textPrimary: "#F1F5F9"
    readonly property color textSecondary: "#64748B"
    readonly property color textMuted: "#475569"

    // ── Font Sizes ──
    readonly property int fontSizeXs: 10
    readonly property int fontSizeSmall: 12
    readonly property int fontSizeBody: 14
    readonly property int fontSizeTitle: 18
    readonly property int fontSizeHeader: 24
    readonly property int fontSizeHero: 32

    // ── Radii ──
    readonly property real cornerRadius: 12.0
    readonly property real cornerRadiusSmall: 8.0

    // ── Animation Durations ──
    readonly property int animFast: 120
    readonly property int animNormal: 200
    readonly property int animSlow: 400

    // ── Shadows & Glow ──
    readonly property real glowRadius: 16.0
    readonly property real glowSpread: 0.0
    readonly property real shadowOffsetY: 4.0
}
