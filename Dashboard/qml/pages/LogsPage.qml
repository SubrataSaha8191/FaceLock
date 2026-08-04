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

        RowLayout {
            Layout.fillWidth: true

            Row {
                spacing: 12
                Layout.fillWidth: true
                Text { text: "☰"; color: Theme.primary; font.pixelSize: Theme.fontSizeHeader }
                Column {
                    Text { text: "Security Audit Trail"; color: Theme.textPrimary; font.pixelSize: Theme.fontSizeHeader; font.bold: true }
                    Text { text: "Structured JSON event log for all security decisions"; color: Theme.textMuted; font.pixelSize: Theme.fontSizeSmall }
                }
            }

            StatusBadge {
                text: "REAL-TIME"
                badgeColor: Theme.info
            }
        }

        GlowCard {
            Layout.fillWidth: true
            Layout.fillHeight: true
            glowColor: Theme.info

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 8

                // Column headers
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Text { text: "EVENT"; color: Theme.textMuted; font.pixelSize: Theme.fontSizeXs; font.bold: true; font.letterSpacing: 1; Layout.preferredWidth: 150 }
                    Text { text: "USER"; color: Theme.textMuted; font.pixelSize: Theme.fontSizeXs; font.bold: true; font.letterSpacing: 1; Layout.preferredWidth: 120 }
                    Text { text: "STATUS"; color: Theme.textMuted; font.pixelSize: Theme.fontSizeXs; font.bold: true; font.letterSpacing: 1; Layout.preferredWidth: 100 }
                    Text { text: "TIMESTAMP"; color: Theme.textMuted; font.pixelSize: Theme.fontSizeXs; font.bold: true; font.letterSpacing: 1; Layout.fillWidth: true }
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: Theme.surfaceBorder }

                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

                    ListView {
                        id: logListView
                        model: [
                            { event: "ENROLLMENT", user: "usr_1", success: true, ts: "10:32:14" },
                            { event: "AUTH_ATTEMPT", user: "usr_1", success: true, ts: "10:33:01" },
                            { event: "LIVENESS_CHECK", user: "usr_2", success: true, ts: "10:34:22" },
                            { event: "AUTH_ATTEMPT", user: "usr_2", success: false, ts: "10:35:45" },
                            { event: "LOCKOUT", user: "usr_2", success: false, ts: "10:35:46" },
                            { event: "PASSWORD_FALLBACK", user: "usr_2", success: true, ts: "10:36:10" }
                        ]
                        spacing: 2

                        delegate: Rectangle {
                            required property var modelData
                            required property int index
                            width: logListView.width
                            height: 36
                            radius: Theme.cornerRadiusSmall
                            color: index % 2 === 0 ? "transparent" : Qt.alpha(Theme.surfaceElevated, 0.5)

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 4
                                spacing: 0

                                // Event type with color coding
                                Text {
                                    text: modelData.event
                                    color: {
                                        if (modelData.event === "LOCKOUT") return Theme.danger
                                        if (modelData.event === "ENROLLMENT") return Theme.primary
                                        if (modelData.event === "AUTH_ATTEMPT") return Theme.warning
                                        return Theme.textSecondary
                                    }
                                    font.pixelSize: Theme.fontSizeSmall
                                    font.bold: true
                                    Layout.preferredWidth: 150
                                }

                                Text {
                                    text: modelData.user
                                    color: Theme.textPrimary
                                    font.pixelSize: Theme.fontSizeSmall
                                    Layout.preferredWidth: 120
                                }

                                StatusBadge {
                                    text: modelData.success ? "OK" : "FAIL"
                                    badgeColor: modelData.success ? Theme.success : Theme.danger
                                    Layout.preferredWidth: 100
                                }

                                Text {
                                    text: modelData.ts
                                    color: Theme.textMuted
                                    font.pixelSize: Theme.fontSizeSmall
                                    font.family: "monospace"
                                    Layout.fillWidth: true
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
