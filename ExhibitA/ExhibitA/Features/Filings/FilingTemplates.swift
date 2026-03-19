import Foundation

struct FilingTemplate {
    let type: FilingType
    let title: String
    let body: String
}

enum FilingTemplateStore {

    static let motions: [FilingTemplate] = [
        FilingTemplate(
            type: .motion,
            title: "Motion to Extend FaceTime by 30 Minutes",
            body: "The plaintiff respectfully moves this court to extend the current FaceTime session by no fewer than thirty (30) additional minutes, on the grounds that the conversation was just getting good and the distance makes every minute count."
        ),
        FilingTemplate(
            type: .motion,
            title: "Motion for Mandatory Goodnight Call",
            body: "The plaintiff moves for a standing order requiring a goodnight phone call every evening, regardless of time zone, schedule, or the defendant's claim of being 'too sleepy.' The court recognizes that hearing each other's voice before sleep is a fundamental right in this relationship."
        ),
        FilingTemplate(
            type: .motion,
            title: "Motion for Coordinated Movie Night",
            body: "The plaintiff petitions this court for an order establishing a synchronized movie night, wherein both parties press play at the agreed-upon time while remaining on FaceTime for real-time commentary, reactions, and the occasional 'are you still watching?'"
        ),
        FilingTemplate(
            type: .motion,
            title: "Motion to Send a Voice Note Instead of Texting",
            body: "The plaintiff respectfully requests that the defendant replace at least one (1) text message per day with a voice note, on the grounds that the plaintiff misses the sound of the defendant's voice and typed words are an insufficient substitute."
        ),
    ]

    static let objections: [FilingTemplate] = [
        FilingTemplate(
            type: .objection,
            title: "Objection: Defendant Has Not Replied in 47 Minutes",
            body: "The plaintiff raises a formal objection on the grounds that the defendant has failed to respond to messages for an unreasonable period of forty-seven (47) minutes. The court notes that the plaintiff has checked their phone no fewer than twelve (12) times during this interval."
        ),
        FilingTemplate(
            type: .objection,
            title: "Objection: Defendant Fell Asleep Without Saying Goodnight",
            body: "The plaintiff lodges a formal objection regarding the defendant's failure to issue a proper goodnight before falling asleep. The court is reminded that silence at the end of a long-distance day is particularly cruel and unusual."
        ),
        FilingTemplate(
            type: .objection,
            title: "Objection: FaceTime Was Too Short Today",
            body: "The plaintiff objects to the duration of today's FaceTime call, which lasted an insufficient period given the current distance between the parties. The plaintiff requests the court take note that 'I have to go' is not a valid legal argument."
        ),
        FilingTemplate(
            type: .objection,
            title: "Objection: Plaintiff Finds Defendant Unreasonably Charming From This Far Away",
            body: "The plaintiff objects to the defendant's continued deployment of charm, wit, and attractiveness from an unreasonable distance, and demands compensation in the form of an expedited visit. Being this charming while being this far away should be a punishable offense."
        ),
    ]

    static let emergencyOrders: [FilingTemplate] = [
        FilingTemplate(
            type: .emergencyOrder,
            title: "Emergency Order: Immediate FaceTime Session Required",
            body: "The plaintiff moves for an emergency order compelling the defendant to initiate a FaceTime call at the earliest possible convenience. The plaintiff's current emotional state requires visual confirmation that the defendant still exists and is still cute."
        ),
        FilingTemplate(
            type: .emergencyOrder,
            title: "Emergency Order: Mandatory 'I Miss You' Text",
            body: "The court is hereby petitioned for an emergency order requiring the defendant to send an 'I miss you' text within the hour. The plaintiff's heart is in contempt of court and only the defendant can restore order."
        ),
        FilingTemplate(
            type: .emergencyOrder,
            title: "Emergency Order: Plaintiff Requires Reassurance",
            body: "The plaintiff requests an emergency order compelling the defendant to provide immediate verbal or written reassurance. The distance has been particularly difficult today and the plaintiff reserves the right to be a little dramatic about it."
        ),
        FilingTemplate(
            type: .emergencyOrder,
            title: "Emergency Order: Virtual Date Night Must Be Scheduled Tonight",
            body: "The court is petitioned for an emergency order mandating a virtual date night this evening, including but not limited to: synchronized dinner, a shared screen activity, and at least fifteen (15) minutes of undivided attention before either party is permitted to fall asleep."
        ),
    ]

    static func templates(for type: FilingType) -> [FilingTemplate] {
        switch type {
        case .motion: motions
        case .objection: objections
        case .emergencyOrder: emergencyOrders
        }
    }
}
