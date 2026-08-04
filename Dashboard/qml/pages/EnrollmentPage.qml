import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import "../themes"

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 28
        spacing: 20

        Row {
            spacing: 12
            Column {
                Text { text: "Biometric Enrollment"; color: Theme.textPrimary; font.pixelSize: Theme.fontSizeHeader; font.bold: true }
                Text { text: "Register a new face template with encrypted zero-knowledge storage"; color: Theme.textSecondary; font.pixelSize: Theme.fontSizeSmall }
            }
        }

        RowLayout {
            spacing: 24
            Layout.fillWidth: true
            Layout.fillHeight: true

            GlowCard {
                Layout.preferredWidth: 340
                Layout.fillHeight: true
                accentGlow: Theme.glassBorder

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 14

                    Text { text: "IDENTITY CREDENTIALS"; color: Theme.textMuted; font.pixelSize: Theme.fontSizeXs; font.bold: true; font.letterSpacing: 1.0 }

                    Text { text: "User ID"; color: Theme.textSecondary; font.pixelSize: Theme.fontSizeSmall }
                    StyledTextField { id: userIdInput; placeholderText: "e.g. usr_101"; Layout.fillWidth: true }

                    Text { text: "Full Name"; color: Theme.textSecondary; font.pixelSize: Theme.fontSizeSmall }
                    StyledTextField { id: usernameInput; placeholderText: "e.g. Alice Smith"; Layout.fillWidth: true }

                    Text { text: "Secret Passphrase"; color: Theme.textSecondary; font.pixelSize: Theme.fontSizeSmall }
                    StyledTextField { id: secretInput; echoMode: TextInput.Password; placeholderText: "Encryption key"; Layout.fillWidth: true }

                    Item { Layout.fillHeight: true }

                    PrimaryButton {
                        text: "Enroll Identity"
                        Layout.fillWidth: true
                        implicitHeight: 44
                        onClicked: {
                            if (typeof facelockBridge !== "undefined") {
                                facelockBridge.enrollUser(userIdInput.text, usernameInput.text, secretInput.text, "")
                            }
                        }
                    }
                }
            }

            GlowCard {
                Layout.fillWidth: true
                Layout.fillHeight: true
                accentGlow: Theme.accent

                Image {
                    id: cameraPreview
                    anchors.fill: parent
                    anchors.margins: 8
                    fillMode: Image.PreserveAspectFit
                    source: "image://livecamera/frame"
                    cache: false

                    Connections {
                        target: typeof facelockBridge !== "undefined" ? facelockBridge : null
                        function onCameraFrameUpdated() {
                            cameraPreview.source = "image://livecamera/frame?" + Math.random()
                        }
                    }
                }

                StatusBadge {
                    text: "CAMERA STREAM"
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.margins: 16
                }
            }
        }
    }
}
