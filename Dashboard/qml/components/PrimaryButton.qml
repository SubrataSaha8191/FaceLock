import QtQuick
import QtQuick.Controls
import "../themes"

Button {
    id: root
    property color btnColor: Theme.primary
    property color hoverColor: Theme.primaryHover
    property color pressColor: Theme.primaryMuted

    implicitWidth: 140
    implicitHeight: 42

    scale: root.pressed ? 0.96 : (root.hovered ? 1.02 : 1.0)
    Behavior on scale { NumberAnimation { duration: Theme.animFast; easing.type: Easing.OutCubic } }

    background: Rectangle {
        radius: Theme.cornerRadiusSmall
        color: root.pressed ? root.pressColor : (root.hovered ? root.hoverColor : root.btnColor)

        Behavior on color { ColorAnimation { duration: Theme.animFast } }

        // Bottom shadow
        Rectangle {
            anchors.fill: parent
            anchors.topMargin: 2
            radius: parent.radius
            color: Qt.alpha("#000000", 0.25)
            z: -1
            visible: !root.pressed
        }
    }

    contentItem: Text {
        text: root.text
        color: Theme.textPrimary
        font.pixelSize: Theme.fontSizeBody
        font.bold: true
        font.letterSpacing: 0.3
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
