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

        // Header
        Row {
            spacing: 12
            Text { text: "◎"; color: Theme.primary; font.pixelSize: Theme.fontSizeHeader }
            Column {
                Text { text: "Biometric Enrollment"; color: Theme.textPrimary; font.pixelSize: Theme.fontSizeHeader; font.bold: true }
                Text { text: "Register a new face template for secure authentication"; color: Theme.textMuted; font.pixelSize: Theme.fontSizeSmall }
            }
        }

        RowLayout {
            spacing: 24
            Layout.fillWidth: true
            Layout.fillHeight: true

            // Form card
            GlowCard {
                Layout.preferredWidth: 320
                Layout.fillHeight: true
                glowColor: Theme.primary

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 20
                    spacing: 14

                    Text { text: "IDENTITY DETAILS"; color: Theme.textMuted; font.pixelSize: Theme.fontSizeXs; font.bold: true; font.letterSpacing: 1.0 }
                    Rectangle { Layout.fillWidth: true; height: 1; color: Theme.surfaceBorder }

                    Text { text: "User ID"; color: Theme.textSecondary; font.pixelSize: Theme.fontSizeSmall }
                    StyledTextField { id: userIdInput; placeholderText: "e.g. usr_101"; Layout.fillWidth: true }

                    Text { text: "Full Name"; color: Theme.textSecondary; font.pixelSize: Theme.fontSizeSmall }
                    StyledTextField { id: usernameInput; placeholderText: "e.g. Alice Smith"; Layout.fillWidth: true }

                    Text { text: "Encryption Passphrase"; color: Theme.textSecondary; font.pixelSize: Theme.fontSizeSmall }
                    StyledTextField { id: secretInput; echoMode: TextInput.Password; placeholderText: "Master secret key"; Layout.fillWidth: true }

                    Item { Layout.fillHeight: true }

                    PrimaryButton {
                        text: "⬤  Enroll Face"
                        Layout.fillWidth: true
                        implicitHeight: 46
                        onClicked: {
                            if (typeof facelockBridge !== "undefined") {
                                facelockBridge.enrollUser(userIdInput.text, usernameInput.text, secretInput.text, "")
                            }
                        }
                    }
                }
            }

            // Camera preview card
            GlowCard {
                Layout.fillWidth: true
                Layout.fillHeight: true
                glowColor: Theme.success

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 6
                    spacing: 0

                    // Camera frame
                    Image {
                        id: cameraPreview
                        Layout.fillWidth: true
                        Layout.fillHeight: true
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
                }

                // Camera overlay badge
                StatusBadge {
                    text: "CAMERA PREVIEW"
                    badgeColor: Theme.success
                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.margins: 14
                }
            }
        }
    }
}
