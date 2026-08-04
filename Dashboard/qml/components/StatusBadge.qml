import QtQuick
import "../themes"

Rectangle {
    id: root
    property string text: "STATUS"
    property color badgeColor: "#161822"

    implicitWidth: badgeText.implicitWidth + 24
    implicitHeight: 22
    radius: Theme.cornerRadiusSmall
    color: root.badgeColor
    border.color: Theme.glassBorder
    border.width: 1

    Row {
        anchors.centerIn: parent
        spacing: 6

        Rectangle {
            width: 6
            height: 6
            radius: 3
            color: Theme.accent
            anchors.verticalCenter: parent.verticalCenter
        }

        Text {
            id: badgeText
            text: root.text
            color: Theme.textPrimary
            font.pixelSize: Theme.fontSizeXs
            font.bold: true
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
