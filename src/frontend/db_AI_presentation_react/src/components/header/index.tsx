import * as Styled from "./styles";
import LogoIcon from "../../assets/imgs/logo_db.png";
import LogoIconDesk from "../../assets/imgs/logo_web.png";
import { useMediaQuery } from "../../hooks/useMediaQuery";

export const Header = () => {
    const isDesktop = useMediaQuery("(min-width: 1024px)");
    const logoSrc = isDesktop ? LogoIconDesk : LogoIcon;

    return (
        <Styled.Container>
            <Styled.Logo src={logoSrc} alt="Logo" />
        </Styled.Container>
    );
};