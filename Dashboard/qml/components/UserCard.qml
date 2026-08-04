import QtQuick
import QtQuick.Controls
import "../themes"

Rectangle {
    id: root
    property string userId: ""
    property string username: ""
    signal deleteRequested(string userId)

    implicitWidth: 340
    implicitHeight: 72
    radius: Theme.cornerRadius
    color: cardHover.containsMouse ? Theme.surfaceElevated : Theme.surface
    border.color: cardHover.containsMouse ? Qt.alpha(Theme.primary, 0.3) : Theme.surfaceBorder
    border.width: 1

    Behavior on color { ColorAnimation { duration: Theme.animNormal } }
    Behavior on border.color { ColorAnimation { duration: Theme.animNormal } }

    Row {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 14

        // Avatar circle with gradient border
        Rectangle {
            width: 44
            height: 44
            radius: 22
            color: "transparent"
            border.width: 2
            border.color: Theme.primary
            anchors.verticalCenter: parent.verticalCenter

            Rectangle {
                anchors.centerIn: parent
                width: 38
                height: 38
                radius: 19
                color: Qt.alpha(Theme.primary, 0.15)

                Text {
                    text: root.username.length > 0 ? root.username.charAt(0).toUpperCase() : "U"
                    color: Theme.primary
                    font.pixelSize: Theme.fontSizeTitle
                    font.bold: true
                    anchors.centerIn: parent
                }
            }
        }

        Column {
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width - 130
            spacing: 3

            Text {
                text: root.username
                color: Theme.textPrimary
                font.pixelSize: Theme.fontSizeBody
                font.bold: true
                elide: Text.ElideRight
                width: parent.width
            }

            Text {
                text: root.userId
                color: Theme.textMuted
                font.pixelSize: Theme.fontSizeXs
                font.letterSpacing: 0.3
                elide: Text.ElideRight
                width: parent.width
            }
        }

        PrimaryButton {
            text: "✕"
            btnColor: Qt.alpha(Theme.danger, 0.15)
            hoverColor: Theme.danger
            pressColor: Qt.alpha(Theme.danger, 0.6)
            implicitWidth: 36
            implicitHeight: 36
            anchors.verticalCenter: parent.verticalCenter
            onClicked: root.deleteRequested(root.userId)

            contentItem: Text {
                text: "✕"
                color: Theme.danger
                font.pixelSize: Theme.fontSizeBody
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    MouseArea {
        id: cardHover
        anchors.fill: parent
        hoverEnabled: true
        propagateComposedEvents: true
        acceptedButtons: Qt.NoButton
    }
}
