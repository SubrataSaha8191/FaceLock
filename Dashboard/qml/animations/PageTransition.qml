import QtQuick
import "../themes"

Item {
    id: root
    property int direction: 1  // 1 = right, -1 = left

    // Enter transition: fade in + slide from side
    Component.onCompleted: {
        enterAnim.start()
    }

    opacity: 0
    transform: Translate { id: slideTranslate; x: root.direction * 30 }

    ParallelAnimation {
        id: enterAnim
        NumberAnimation {
            target: root
            property: "opacity"
            from: 0; to: 1
            duration: Theme.animSlow
            easing.type: Easing.OutCubic
        }
        NumberAnimation {
            target: slideTranslate
            property: "x"
            from: root.direction * 30; to: 0
            duration: Theme.animSlow
            easing.type: Easing.OutCubic
        }
    }
}
