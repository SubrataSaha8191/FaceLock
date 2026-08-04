import QtQuick
import QtQuick.Effects
import "../themes"

Rectangle {
    id: root
    property bool glowOnHover: true
    property color glowColor: Theme.surfaceGlow

    radius: Theme.cornerRadius
    color: Theme.surface
    border.color: hoverArea.containsMouse ? Qt.alpha(glowColor, 0.5) : Theme.surfaceBorder
    border.width: hoverArea.containsMouse ? 1.5 : 1

    Behavior on border.color {
        ColorAnimation { duration: Theme.animNormal }
    }

    // Subtle inner gradient overlay
    Rectangle {
        anchors.fill: parent
        radius: parent.radius
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.alpha(root.glowColor, 0.03) }
            GradientStop { position: 1.0; color: "transparent" }
        }
    }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: root.glowOnHover
        propagateComposedEvents: true
        acceptedButtons: Qt.NoButton
    }
}
