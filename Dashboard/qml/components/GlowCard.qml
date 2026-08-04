import QtQuick
import "../themes"

Rectangle {
    id: root
    property bool glowOnHover: true
    property color accentGlow: Theme.glassBorder

    radius: Theme.cornerRadius
    color: hoverArea.containsMouse ? Theme.cardHover : Theme.cardBackground
    border.color: hoverArea.containsMouse ? Theme.accent : root.accentGlow
    border.width: 1

    Behavior on color { ColorAnimation { duration: Theme.animFast } }
    Behavior on border.color { ColorAnimation { duration: Theme.animFast } }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: root.glowOnHover
        propagateComposedEvents: true
        acceptedButtons: Qt.NoButton
    }
}
