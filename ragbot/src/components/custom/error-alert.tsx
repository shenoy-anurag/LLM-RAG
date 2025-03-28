import { AlertCircle } from "lucide-react"

import {
    Alert,
    AlertDescription,
    AlertTitle,
} from "@/components/ui/alert"
import ButtonMailto from "@/components/custom/mailto"

export function AlertDestructive() {
    const ADMIN_EMAIL: string = import.meta.env.VITE_ADMIN_EMAIL;
    const subject: string = "subject=Error: Medquad RAG Chatbot";
    const body: string = "body=Hi Anurag,\n I encountered an issue when using your Medical FAQ Chatbot. \n\n I have attached a screenshot of the issue. \n\n Thank you,<your_name>"
    const MAIL_TO: string = "mailto:" + ADMIN_EMAIL + "?" + subject + "&" + body;

    return (
        <Alert variant="destructive" className="px-6 py-4">
            <AlertCircle className="h-6 w-6" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
                It seems there's an issue with the backend deployment.
                You can try to refresh the page, and see if the issue persists.
                <br />
                If it still persists, please drop me an email at <ButtonMailto mailto={MAIL_TO} label={ADMIN_EMAIL} />
            </AlertDescription>
        </Alert>
    )
}
