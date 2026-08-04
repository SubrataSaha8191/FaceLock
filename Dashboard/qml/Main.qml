import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"
import "pages"
import "themes"

ApplicationWindow {
    id: window
    width: 1120
    height: 720
    visible: true
    title: "FaceLock — Biometric Security Dashboard"
    color: Theme.background

    RowLayout {
        anchors.fill: parent
        spacing: 0

        NavigationBar {
            id: navBar
            Layout.fillHeight: true
            onPageSelected: function(idx) {
                pageLayout.currentIndex = idx
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // Premium status bar
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 44
                color: Theme.surface
                border.color: Theme.surfaceBorder
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 24
                    anchors.rightMargin: 24

                    Text {
                        id: statusText
                        text: "System Ready"
                        color: Theme.textSecondary
                        font.pixelSize: Theme.fontSizeSmall
                        Layout.fillWidth: true
                    }

                    // Live clock
                    Text {
                        id: clockText
                        color: Theme.textMuted
                        font.pixelSize: Theme.fontSizeXs
                        font.letterSpacing: 0.5

                        Timer {
                            interval: 1000
                            running: true
                            repeat: true
                            triggeredOnStart: true
                            onTriggered: {
                                var d = new Date()
                                clockText.text = d.toLocaleTimeString(Qt.locale(), "HH:mm:ss")
                            }
                        }
                    }

                    Item { width: 16 }

                    StatusBadge {
                        text: "PROTECTED"
                        badgeColor: Theme.success
                    }
                }
            }

            // Page content with fade transition
            StackLayout {
                id: pageLayout
                currentIndex: 0
                Layout.fillWidth: true
                Layout.fillHeight: true

                onCurrentIndexChanged: {
                    for (var i = 0; i < children.length; i++) {
                        children[i].opacity = (i === currentIndex) ? 1 : 0
                    }
                }

                DashboardPage { Behavior on opacity { NumberAnimation { duration: Theme.animSlow } } }
                EnrollmentPage { Behavior on opacity { NumberAnimation { duration: Theme.animSlow } } }
                CameraPreviewPage { Behavior on opacity { NumberAnimation { duration: Theme.animSlow } } }
                SettingsPage { Behavior on opacity { NumberAnimation { duration: Theme.animSlow } } }
                LogsPage { Behavior on opacity { NumberAnimation { duration: Theme.animSlow } } }
            }
        }
    }

    Connections {
        target: typeof facelockBridge !== "undefined" ? facelockBridge : null
        function onStatusMessageChanged(message, isSuccess) {
            statusText.text = message
            statusText.color = isSuccess ? Theme.success : Theme.danger
        }
    }
}
