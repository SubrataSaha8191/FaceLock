import QtQuick
import QtQuick.Controls
import "../themes"

Rectangle {
    id: root
    property string userId: ""
    property string username: ""
    signal deleteRequested(string userId)

    implicitWidth: 500
    implicitHeight: 48
    radius: Theme.cornerRadiusSmall
    color: cardHover.containsMouse ? Theme.cardHover : Theme.cardBackground
    border.color: cardHover.containsMouse ? Theme.accent : Theme.glassBorder
    border.width: 1

    Behavior on color { ColorAnimation { duration: Theme.animFast } }

    Row {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        spacing: 12

        Rectangle {
            width: 28; height: 28; radius: 4
            color: "#181B26"
            border.color: Theme.accent; border.width: 1
            anchors.verticalCenter: parent.verticalCenter

            Text {
                text: root.username.length > 0 ? root.username.substring(0, 2).toUpperCase() : "US"
                color: Theme.accent
                font.pixelSize: 11
                font.bold: true
                anchors.centerIn: parent
            }
        }

        Text {
            text: root.username
            color: Theme.textPrimary
            font.pixelSize: Theme.fontSizeSmall
            font.bold: true
            anchors.verticalCenter: parent.verticalCenter
            width: 140
            elide: Text.ElideRight
        }

        Rectangle {
            implicitWidth: 74; implicitHeight: 20; radius: 4
            color: "#181B26"; border.color: Theme.glassBorder; border.width: 1
            anchors.verticalCenter: parent.verticalCenter

            Text {
                text: "AES-256"
                color: Theme.textMuted
                font.pixelSize: 10
                anchors.centerIn: parent
            }
        }

        Text {
            text: "ID: " + root.userId
            color: Theme.textMuted
            font.pixelSize: Theme.fontSizeXs
            anchors.verticalCenter: parent.verticalCenter
            elide: Text.ElideRight
            width: 100
        }

        Item { width: 1; height: 1 }

        Rectangle {
            width: 26; height: 26; radius: 4
            color: deleteHover.containsMouse ? Qt.rgba(239, 68, 68, 0.2) : "transparent"
            border.color: deleteHover.containsMouse ? Theme.danger : "transparent"
            border.width: 1
            anchors.verticalCenter: parent.verticalCenter

            VectorIcon {
                name: "close"
                iconColor: deleteHover.containsMouse ? Theme.danger : Theme.textMuted
                implicitWidth: 12; implicitHeight: 12
                anchors.centerIn: parent
            }

            MouseArea {
                id: deleteHover
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: root.deleteRequested(root.userId)
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
