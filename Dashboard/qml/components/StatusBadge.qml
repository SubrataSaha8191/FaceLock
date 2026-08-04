import QtQuick
import QtQuick.Controls
import "../themes"

Rectangle {
    id: root
    property string text: "Active"
    property color badgeColor: Theme.success

    implicitWidth: label.implicitWidth + 32
    implicitHeight: 26
    radius: 13
    color: Qt.alpha(badgeColor, 0.12)
    border.color: Qt.alpha(badgeColor, 0.4)
    border.width: 1

    Row {
        anchors.centerIn: parent
        spacing: 6

        Rectangle {
            width: 7
            height: 7
            radius: 3.5
            color: root.badgeColor
            anchors.verticalCenter: parent.verticalCenter

            // Pulse animation on the live dot
            SequentialAnimation on opacity {
                loops: Animation.Infinite
                NumberAnimation { to: 0.4; duration: 800; easing.type: Easing.InOutSine }
                NumberAnimation { to: 1.0; duration: 800; easing.type: Easing.InOutSine }
            }
        }

        Text {
            id: label
            text: root.text
            color: root.badgeColor
            font.pixelSize: Theme.fontSizeXs
            font.bold: true
            font.letterSpacing: 0.5
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
