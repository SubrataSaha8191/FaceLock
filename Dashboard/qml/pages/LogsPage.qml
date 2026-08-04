import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import "../themes"

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            Column {
                Text { text: "Security Audit Log"; color: Theme.textPrimary; font.pixelSize: Theme.fontSizeHeader; font.bold: true }
                Text { text: "Real-time security authentication event log"; color: Theme.textSecondary; font.pixelSize: Theme.fontSizeSmall }
            }
            Item { Layout.fillWidth: true }
            StatusBadge { text: "Realtime Feed" }
        }

        GlowCard {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 16
                spacing: 8

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    Text { text: "EVENT"; color: Theme.textMuted; font.pixelSize: Theme.fontSizeXs; font.bold: true; Layout.preferredWidth: 150 }
                    Text { text: "USER"; color: Theme.textMuted; font.pixelSize: Theme.fontSizeXs; font.bold: true; Layout.preferredWidth: 120 }
                    Text { text: "STATUS"; color: Theme.textMuted; font.pixelSize: Theme.fontSizeXs; font.bold: true; Layout.preferredWidth: 100 }
                    Text { text: "TIMESTAMP"; color: Theme.textMuted; font.pixelSize: Theme.fontSizeXs; font.bold: true; Layout.fillWidth: true }
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: Theme.glassBorder }

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
                            height: 38
                            radius: Theme.cornerRadiusSmall
                            color: index % 2 === 0 ? "transparent" : Qt.rgba(1, 1, 1, 0.04)

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 8
                                spacing: 0

                                Text {
                                    text: modelData.event
                                    color: Theme.textPrimary
                                    font.pixelSize: Theme.fontSizeSmall
                                    font.bold: true
                                    Layout.preferredWidth: 150
                                }

                                Text {
                                    text: modelData.user
                                    color: Theme.textSecondary
                                    font.pixelSize: Theme.fontSizeSmall
                                    Layout.preferredWidth: 120
                                }

                                StatusBadge {
                                    text: modelData.success ? "OK" : "FAIL"
                                    Layout.preferredWidth: 100
                                }

                                Text {
                                    text: modelData.ts
                                    color: Theme.textMuted
                                    font.pixelSize: Theme.fontSizeSmall
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
