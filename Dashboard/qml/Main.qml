import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"
import "pages"
import "themes"

ApplicationWindow {
    id: window
    width: 1240
    height: 780
    visible: true
    title: "FaceLock Platform"
    color: Theme.background

    // Animated Aurora Glow Background Layer
    AuroraBackground {}

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

            // Top Header Bar
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 56
                color: Qt.rgba(0.08, 0.09, 0.12, 0.6)

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 20
                    anchors.rightMargin: 20
                    spacing: 14

                    StyledTextField {
                        id: searchField
                        placeholderText: "Search identities, events..."
                        iconName: "search"
                        implicitWidth: 260
                    }

                    Item { Layout.fillWidth: true }

                    PrimaryButton {
                        text: "+ Enroll User"
                        implicitWidth: 110
                        onClicked: navBar.pageSelected(1)
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Theme.glassBorder
            }

            // Main Views Stack
            StackLayout {
                id: pageLayout
                currentIndex: 0
                Layout.fillWidth: true
                Layout.fillHeight: true

                DashboardPage {}
                EnrollmentPage {}
                CameraPreviewPage {}
                SettingsPage {}
                LogsPage {}
            }
        }
    }
}
