import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../themes"

Rectangle {
    id: root
    property int currentIndex: 0
    signal pageSelected(int index)

    width: 210
    color: Theme.sidebarBackground
    border.color: Theme.glassBorder
    border.width: 1

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 12

        // Top Brand Header (Inspired by HUBTOWN / Noomo typography)
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Rectangle {
                implicitWidth: 32; implicitHeight: 32; radius: 4
                color: "#181A24"
                border.color: Theme.accent; border.width: 1

                VectorIcon {
                    name: "brand"
                    iconColor: Theme.accent
                    implicitWidth: 16; implicitHeight: 16
                    anchors.centerIn: parent
                }
            }

            Column {
                Text { text: "FACELOCK"; color: Theme.textPrimary; font.pixelSize: 13; font.bold: true; font.letterSpacing: 1 }
                Text { text: "CORE PLATFORM"; color: Theme.textMuted; font.pixelSize: 9; font.letterSpacing: 0.5 }
            }
        }

        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: Theme.glassBorder }

        Text {
            text: "SYSTEM NAVIGATION"
            color: Theme.textMuted
            font.pixelSize: 9
            font.bold: true
            font.letterSpacing: 1
            Layout.topMargin: 4
        }

        Repeater {
            model: [
                { label: "Overview",   icon: "dashboard" },
                { label: "Enrollment", icon: "enrollment" },
                { label: "Perception", icon: "camera" },
                { label: "Settings",   icon: "settings" },
                { label: "Audit Logs", icon: "logs" }
            ]

            Button {
                required property int index
                required property var modelData

                Layout.fillWidth: true
                implicitHeight: 38

                background: Rectangle {
                    radius: Theme.cornerRadiusSmall
                    color: root.currentIndex === index
                        ? "#181B26"
                        : (hovered ? "#141620" : "transparent")
                    border.color: root.currentIndex === index ? Qt.rgba(0, 240, 255, 0.4) : "transparent"
                    border.width: root.currentIndex === index ? 1 : 0

                    Rectangle {
                        visible: root.currentIndex === index
                        width: 3; height: 20; radius: 1.5
                        color: Theme.accent
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                contentItem: Row {
                    spacing: 12
                    leftPadding: 12

                    VectorIcon {
                        name: modelData.icon
                        iconColor: root.currentIndex === index ? Theme.accent : Theme.textMuted
                        implicitWidth: 16; implicitHeight: 16
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Text {
                        text: modelData.label
                        color: root.currentIndex === index ? Theme.textPrimary : Theme.textSecondary
                        font.pixelSize: Theme.fontSizeSmall
                        font.bold: root.currentIndex === index
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                onClicked: {
                    root.currentIndex = index
                    root.pageSelected(index)
                }
            }
        }

        Item { Layout.fillHeight: true }
    }
}
