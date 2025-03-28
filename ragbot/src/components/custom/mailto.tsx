import React from "react";
import { Link } from "react-router-dom";

interface ButtonMailtoProps {
    mailto: string;
    label: string;
}

const ButtonMailto: React.FC<ButtonMailtoProps> = ({ mailto, label }) => {
    return (
        <Link
            to='#'
            onClick={(e) => {
                window.location.href = mailto;
                e.preventDefault();
            }}
        >
            {label}
        </Link>
    );
};

export default ButtonMailto;