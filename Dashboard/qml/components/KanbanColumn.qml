import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../themes"

Rectangle {
    id: root
    property string title: "Column"
    property string countText: "0"
    property string actionText: "+ Add item"
    signal actionTriggered()
    default property alias columnChildren: contentLayout.children

    radius: Theme.cornerRadiusColumn
    color: Theme.glassColumn
    border.color: Theme.glassBorder
    border.width: 1

    Layout.fillWidth: true
    Layout.fillHeight: true

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 12

        // Column Header (Matching Image #2: 'App intake 3' + trash icon)
        RowLayout {
            Layout.fillWidth: true
            Text {
                text: root.title
                color: Theme.textPrimary
                font.pixelSize: Theme.fontSizeBody
                font.bold: true
            }
            Rectangle {
                width: 18; height: 18; radius: 9
                color: Qt.rgba(1, 1, 1, 0.1)
                Text {
                    text: root.countText
                    color: Theme.textMuted
                    font.pixelSize: 10
                    font.bold: true
                    anchors.centerIn: parent
                }
            }
            Item { Layout.fillWidth: true }
            VectorIcon {
                name: "trash"
                iconColor: Theme.textMuted
                implicitWidth: 14
                implicitHeight: 14
            }
        }

        // Inner Child Content Stack
        ColumnLayout {
            id: contentLayout
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10
        }

        // Column Footer Button (Matching '+ Add new loan' in Image #2)
        Row {
            spacing: 6
            VectorIcon {
                name: "plus"
                iconColor: Theme.textMuted
                implicitWidth: 12
                implicitHeight: 12
                anchors.verticalCenter: parent.verticalCenter
            }
            Text {
                text: root.actionText
                color: Theme.textMuted
                font.pixelSize: Theme.fontSizeSmall
                anchors.verticalCenter: parent.verticalCenter
            }
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: root.actionTriggered()
            }
        }
    }
}
