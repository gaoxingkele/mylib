%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% %%	Document class for publication in Tech Science Press
%% %%	Upadated on 09 Jan 2025
%% %%	Version 2026.1.2.4Beta
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%% Identification
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{Definitions/tsp}[05/01/2026 TSP paper class]

%% Preliminary declarations
\LoadClass[11pt,letterpaper]{article}
\RequirePackage[T1]{fontenc}
\RequirePackage[utf8]{inputenc}
\RequirePackage{calc}
\RequirePackage{textgreek}
\RequirePackage{indentfirst}
\RequirePackage{fancyhdr}
\RequirePackage{graphicx,epstopdf}
\RequirePackage{lastpage}
\RequirePackage{ifthen}
%\RequirePackage{lineno}
\RequirePackage[right,mathlines]{lineno}
\RequirePackage{float}
\RequirePackage[fleqn]{amsmath} % flush left equations
\RequirePackage{amssymb} % For math environment bold format
\setlength{\mathindent}{0pt} % equations indentation
\RequirePackage{setspace}
\RequirePackage{enumitem}
\RequirePackage{libertine}
\RequirePackage{libertinust1math} % Libertine math 2025.10.22
%\RequirePackage{EB Garamond} % font
%\RequirePackage{libertine} 
%\RequirePackage{newtxmath}
%\RequirePackage{newtxmath}
%\RequirePackage{tgbonum}
%\RequirePackage{mathpazo} 
\RequirePackage{booktabs} % for \toprule etc. in tables
\RequirePackage{titlesec}
\RequirePackage{etoolbox} % \AtBeginDocument etc.
\RequirePackage{xcolor, colortbl} % \textcolor{red}{This is red text.}  \colorbox{yellow}{This is highlighted text with a yellow background.} \definecolor{myblue}{RGB}{0, 128, 255} \textcolor{myblue}{This is a custom blue color.}
\RequirePackage{soul} % \hl{text} \st{text} \ul{text} \so{text} \setul \setst \sethl...
\newcommand{\highlighting}[1]{\colorbox{yellow}{#1}}
\RequirePackage{multirow}
\RequirePackage{microtype} %  \textls[]{}
\RequirePackage{tikz} % For \foreach used for Orcid icon
\RequirePackage{refcount} % To enable extracting the value of the counter "LastPage" 
\RequirePackage{totcount} % To enable extracting the value of the counter "page" 
\RequirePackage{attrib} % For XML2PDF use \tag{} for equation
\RequirePackage{upgreek} % For making greek letters not italic
\RequirePackage{array} % For table array
\RequirePackage{tabularx}
\RequirePackage{pbox} % For biography environment
\RequirePackage{ragged2e} % For command \justifying
\RequirePackage[subfigure]{tocloft} % For dots in TOC. If subfigure package is loaded, the subfigure option needs to be added here to avoid clash: if not, use \RequirePackage[]{tocloft}
\RequirePackage[labelformat=simple]{subfig} % Support to add subfigures
\RequirePackage{adjustbox}
\RequirePackage{enotez} %  \printendnotes[custom]
 %\RequirePackage{tabto} % To use tabto for aff and corres
%\RequirePackage{changepage}

%% Options
\def\@continuouspages{}
\newcommand{\continuouspages}[1]{\gdef\@continuouspages{#1}}

%% Options
%% To choose the journal
%% All journals (website name, full name, short name, DOI abbreviation, and ISSN + choice of continuous page numbers) are defined in journalnames.tex. 
\input{Definitions/journalnames}
\DeclareOption{journal}{\ClassWarning{tsp}{You used an invalid journal name or you have not specified the journal. The first option of the documentclass command specifies the journal. The word 'journal' should be replaced by one of the journal names specified in template.tex (in the comment 'Choose between the following TSP journal').}} 

%% To choose the type of paper
\DeclareOption{abstract}{\gdef\@arttype{ABSTRACT}}
\DeclareOption{analysis}{\gdef\@arttype{ANALYSIS}}
\DeclareOption{article}{\gdef\@arttype{ARTICLE}}
\DeclareOption{biographicalitem}{\gdef\@arttype{BIOGRAPHICAL ITEM}}
\DeclareOption{casereport}{\gdef\@arttype{CASE REPORT}}
%\DeclareOption{comment}{\gdef\@arttype{COMMENT}} %Not applied
\DeclareOption{commentary}{\gdef\@arttype{COMMENTARY}}
\DeclareOption{communication}{\gdef\@arttype{COMMUNICATION}}
%\DeclareOption{conferenceproceedings}{\gdef\@arttype{PROCEEDINGS}} %Not applicable
\DeclareOption{correction}{\gdef\@arttype{CORRECTION}}
%\DeclareOption{conferencereport}{\gdef\@arttype{CONFERENCE REPORT}} %Not applicable
%\DeclareOption{expressionofconcern}{\gdef\@arttype{EXPRESSION OF CONCERN}} %Not applicable
%\DeclareOption{meetingreport}{\gdef\@arttype{MEETING REPORT}} %Not applicable
%\DeclareOption{datadescriptor}{\gdef\@arttype{DATA DESCRIPTOR}} %Not applicable
%\DeclareOption{discussion}{\gdef\@arttype{DISCUSSION}} %Not applicable
\DeclareOption{editorial}{\gdef\@arttype{EDITORIAL}}
\DeclareOption{guideline}{\gdef\@arttype{GUIDELINE}}
\DeclareOption{howidoit}{\gdef\@arttype{HOW I DO IT}} %Only for CJU
\DeclareOption{introduction}{\gdef\@arttype{INTRODUCTION}}
\DeclareOption{letter}{\gdef\@arttype{LETTER}}
\DeclareOption{legends}{\gdef\@arttype{LEGENDS}} %Only for CJU
\DeclareOption{minireview}{\gdef\@arttype{MINI REVIEW}}
\DeclareOption{openforum}{\gdef\@arttype{OPEN FORUM}}
\DeclareOption{perspective}{\gdef\@arttype{PERSPECTIVE}}
\DeclareOption{proceedings}{\gdef\@arttype{PROCEEDINGS}}
\DeclareOption{protocol}{\gdef\@arttype{PROTOCOL}}
%\DeclareOption{reply}{\gdef\@arttype{REPLY}} %Not applicable
\DeclareOption{retraction}{\gdef\@arttype{RETRACTION}}
\DeclareOption{review}{\gdef\@arttype{REVIEW}}
\DeclareOption{shortcommunication}{\gdef\@arttype{SHORT COMMUNICATION}}
\DeclareOption{technicalreport}{\gdef\@arttype{TECHNICAL REPORT}}
\DeclareOption{theory}{\gdef\@arttype{THEORY}}
\DeclareOption{tutorial}{\gdef\@arttype{TUTORIAL}}
\DeclareOption{viewpoint}{\gdef\@arttype{VIEWPOINT}}

%% To choose the status of the paper
\DeclareOption{submit}{\gdef\@status{submit}}
\DeclareOption{accept}{\gdef\@status{accept}}

%% To choose the whether there is one or more authors
\DeclareOption{oneauthor}{\gdef\@authornum{Author}}
\DeclareOption{moreauthors}{\gdef\@authornum{Authors}}

%% Add the chosen options to the class
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}

%% Defaults
\ExecuteOptions{notspecified,11pt,letterpaper,article,submit,oneauthor}

%% Process options
\ProcessOptions\relax

%% More declarations
%% Maths environments
\RequirePackage{amsthm}
\newtheoremstyle{tsp}% name
{12pt}% space above
{12pt}% space below
{\itshape}% body font
{}% indent amount 1
{\bfseries}% theorem head font
{:}% punctuation after theorem head
{0.5em}% space after theorem head
{}% theorem head spec (can be left empty, meaning 'normal')

\renewcommand{\qed}{\unskip\nobreak\enspace\qedsymbol} %% This places the symbol right after the text instead of placing it at the end on the line.

\renewenvironment{proof}[1][\proofname]{\par %% \proofname allows to have "Proof of my theorem"
  \pushQED{\qed}%
  \normalfont \topsep6\p@\@plus6\p@\relax
  \trivlist
  \item[\hskip\labelsep
	\bfseries%% "Proof" is bold
	 #1\@addpunct{:}]\ignorespaces
}{%
\popQED\endtrivlist\@endpefalse
}

 \theoremstyle{tsp}
 \newcounter{theorem}
 \setcounter{theorem}{0}
 \newtheorem{Theorem}[theorem]{Theorem}
 
 \newcounter{lemma}
 \setcounter{lemma}{0}
 \newtheorem{Lemma}[lemma]{Lemma}
 
 \newcounter{corollary}
 \setcounter{corollary}{0}
 \newtheorem{Corollary}[corollary]{Corollary}
 
 \newcounter{proposition}
 \setcounter{proposition}{0}
 \newtheorem{Proposition}[proposition]{Proposition}
 
 \newcounter{characterization}
 \setcounter{characterization}{0}
 \newtheorem{Characterization}[characterization]{Characterization}
 
 \newcounter{property}
 \setcounter{property}{0}
 \newtheorem{Property}[property]{Property}
 
 \newcounter{problem}
 \setcounter{problem}{0}
 \newtheorem{Problem}[problem]{Problem}
 
 \newcounter{example}
 \setcounter{example}{0}
 \newtheorem{Example}[example]{Example}
 
 \newcounter{examplesanddefinitions}
 \setcounter{examplesanddefinitions}{0}
 \newtheorem{ExamplesandDefinitions}[examplesanddefinitions]{Examples and Definitions}
 
 \newcounter{remark}
 \setcounter{remark}{0}
 \newtheorem{Remark}[remark]{Remark}
 
 \newcounter{definition}
 \setcounter{definition}{0}
 \newtheorem{Definition}[definition]{Definition}
 
 \newcounter{hypothesis}
 \setcounter{hypothesis}{0}
 \newtheorem{Hypothesis}[hypothesis]{Hypothesis}

 \newcounter{notation}
 \setcounter{notation}{0}
 \newtheorem{Notation}[notation]{Notation}
 
 \newcounter{assumption}
 \setcounter{assumption}{0}
 \newtheorem{Assumption}[assumption]{Assumption}

 \newcounter{algorithm}
 \setcounter{algorithm}{0}
 \newtheorem{Algorithm}[algorithm]{Algorithm}

%% Define left/right mark in math environment
\let\originalleft\left
\let\originalright\right
\renewcommand{\left}{\mathopen{}\mathclose\bgroup\originalleft}
\renewcommand{\right}{\aftergroup\egroup\originalright}


%% APA style journals:  for APA style journals
%\newcommand{\isAPAStyle}{
%	\ifthenelse{\equal{\@journal}{jpa} 
%		}
%}

%% References:  for APA style journals
%\isAPAStyle{%
%\RequirePackage[natbibapa]{Definitions/apacite} % For APA style journals
%          }{%
%          \RequirePackage[sort&compress,sectionbib]{natbib}
%} % Option sectionbib is for optionally organizing references using sections (author request)


%\isAPAStyle{%
%      \bibliographystyle{Definitions/apacite}
%          }{%
%	            \bibliographystyle{Definitions/vancouver}
%	            \bibpunct{[}{]}{,}{n}{}{,}%
%       }%
%}
 
%% References
\RequirePackage[sort&compress,sectionbib]{natbib} % Option sectionbib is for optionally organizing references using sections (author request)

%% Vancouver style for all journals
\bibliographystyle{Definitions/vancouver}
\bibpunct{[}{]}{,}{n}{}{,}%

\renewcommand\NAT@set@cites{%
  \ifNAT@numbers
    \ifNAT@super \let\@cite\NAT@citesuper
       \def\NAT@mbox##1{\unskip\nobreak\textsuperscript{##1}}%
       \let\citeyearpar=\citeyear
       \let\NAT@space\relax
       \def\NAT@super@kern{\kern\p@}%
    \else
       \let\NAT@mbox=\mbox
       \let\@cite\NAT@citenum
       \let\NAT@space\relax
       \let\NAT@super@kern\relax
    \fi
    \let\@citex\NAT@citexnum
    \let\@biblabel\NAT@biblabelnum
    \let\@bibsetup\NAT@bibsetnum
    \renewcommand\NAT@idxtxt{\NAT@name\NAT@spacechar\NAT@open\NAT@num\NAT@close}%
    \def\natexlab##1{}%
    \def\NAT@penalty{\penalty\@m}%
  \else
    \let\@cite\NAT@cite
    \let\@citex\NAT@citex
    \let\@biblabel\NAT@biblabel
    \let\@bibsetup\NAT@bibsetup
    \let\NAT@space\NAT@spacechar
    \let\NAT@penalty\@empty
    \renewcommand\NAT@idxtxt{\NAT@name\NAT@spacechar\NAT@open\NAT@date\NAT@close}%
    \def\natexlab##1{##1}%
  \fi}% Could be removed


%% Hyperlinks
%% Define color for citations
\definecolor{bluecite}{HTML}{0875b7}

% After TeXLive 2021, \AddToHook{begindocument} is needed to make sure that hyperref is loaded last. \ifdef{\AddToHook{begindocument}}{ is needed for backwards-compatibility because \AddToHook{begindocument} did not yet exist in 2020.
% After TeXLive 2022, \AddToHook{begindocument/before}{} is needed and  \DeclareHookRule{begindocument}{hyperref}{before}{tsp} needs to be added because of the new version of hyperref.
% Simplified version for loading hyperref package
\newcommand{\hyperrefpackage}{
  \RequirePackage[unicode=true,
    bookmarksopen=true,
    pdffitwindow=true,
    colorlinks=true,
    linkcolor=bluecite,
    citecolor=bluecite,
    urlcolor=bluecite,
    hyperfootnotes=false,
    pdfstartview={FitH},
    pdfpagemode=UseNone]{hyperref}
\RequirePackage[capitalise]{cleveref}
}


%% Ensure \hyperrefpackage is loaded before document starts
\ifdef{\AddToHook}{
  \DeclareHookRule{begindocument}{hyperref}{before}{tsp}
  \AddToHook{begindocument/before}{
    \hyperrefpackage
  }
}{
  \hyperrefpackage
}

%% To have the possibility to change the urlcolor
\newcommand{\changeurlcolor}[1]{\hypersetup{urlcolor=#1}} 

%% New crefnamedefinitions
\newcommand{\crefnameDefinitions}{
	\crefname{figure}{Fig.}{Figs.}
	\crefname{table}{Table}{Tables}
	\crefname{section}{Section}{Sections}
	\crefname{appendix}{Appendix}{Appendices}
	\crefname{scheme}{Scheme}{Schemes}
	\crefname{chart}{Chart}{Charts}
	\crefname{photo}{Photo}{Photos}
	\crefname{paragraph}{Section}{Sections}
}

%% Cleveref definitions
\newcommand{\cleverefDefinitions}{
	\crefrangelabelformat{figure}{##3##1##4--##5##2##6} % double # for nesting inside \newcommand
	\crefrangelabelformat{table}{##3##1##4--##5##2##6}
	\crefrangelabelformat{section}{##3##1##4--##5##2##6}	
	\crefrangelabelformat{appendix}{##3##1##4--##5##2##6}
	\crefrangelabelformat{scheme}{##3##1##4--##5##2##6}
	\crefrangelabelformat{chart}{##3##1##4--##5##2##6}
	\crefrangelabelformat{photo}{##3##1##4--##5##2##6}
}

\newcommand{\crefrangeconjunction}{--}
\newcommand{\fig}[1]{Fig.~\ref{#1}}
\newcommand{\tabref}[1]{Table~\ref{#1}}
\newcommand{\sect}[1]{Section~\ref{#1}}
\newcommand{\app}[1]{Appendix~\ref{#1}}
\newcommand{\sche}[1]{Scheme~\ref{#1}}
\newcommand{\cchart}[1]{Chart~\ref{#1}}
\newcommand{\cphoto}[1]{Photo~\ref{#1}}
\newcommand{\equ}[1]{\ref{#1}}
\newcommand{\boxref}[1]{Box~\ref{#1}}

%% Metadata
\newcommand{\org@maketitle}{}% LaTex-Check
\let\org@maketitle\maketitle
\def\maketitle{%
	\hypersetup{
		pdftitle={\@Title},
		pdfsubject={\@abstract},
		pdfkeywords={\@keyword},
		pdfauthor={\@AuthorNames}
		}%
	\org@maketitle
}


%% \endnote{} \printendnotes[custom]
\setenotez{backref=true}
\DeclareInstance{enotez-list}{custom}{paragraph}{
	format=\fontsize{9}{9}\selectfont\leftskip0.76cm,
	number=\textsuperscript{#1} \hspace{4.7mm},
	notes-sep=0pt
}

%% \footnote{}
\RequirePackage[hang]{footmisc}
\setlength{\skip\footins}{1.2cm}
\setlength{\footnotemargin}{5mm}
\def\footnoterule{\kern-14\p@
\hrule \@width 2in \kern 11.6\p@}

%% URL old
%\RequirePackage{url}
%\urlstyle{same}
%\g@addto@macro{\UrlBreaks}{\UrlOrds} 

%% URL new
\RequirePackage{url}
\urlstyle{same}
% Line breaks in URL
\def\UrlDigits{\do\1\do\2\do\3\do\4\do\5\do\6\do\7\do\8\do\9\do\0}
\g@addto@macro{\UrlBreaks}{\UrlOrds}
\g@addto@macro{\UrlBreaks}{\UrlDigits}


%% Widows & orphans
\clubpenalty=10000
\widowpenalty=10000
\displaywidowpenalty=10000

%% To avoid "Output-loop.." compile bug
\maxdeadcycles=10000


%% Front matter
% Command for checking for a question mark or exclamation mark in title (not applicable now)
\def\instring#1#2{TT\fi\begingroup\edef\x{\endgroup\noexpand\in@{#1}{#2}}\x\ifin@}

\newcommand{\firstargument}{}
\newcommand{\Title}[1]{\gdef\@Title{#1}}%
\newcommand{\Author}[1]{\gdef\@Author{#1}}%
\def\@AuthorNames{}
\newcommand{\AuthorNames}[1]{\gdef\@AuthorNames{#1}}%
\newcommand{\firstpage}[1]{\gdef\@firstpage{#1}}
\newcommand{\lastpage}[1]{\gdef\@lastpage{#1}}
\newcommand{\doinum}[1]{\gdef\@doinum{#1}}
\newcommand{\hreflink}[1]{\gdef\@hreflink{#1}}
\def\@AuthorCitation{}
\newcommand{\AuthorCitation}[1]{\gdef\@AuthorCitation{#1}}%
\def\@TitleCitation{}
\newcommand{\TitleCitation}[1]{\gdef\@TitleCitation{#1}}%
\newcommand{\papercitation}{%
    \@AuthorCitation. \@TitleCitation. \@journalshort. \@pubyear;%
    \@pubvolume%
    \ifthenelse{\equal{\@issuenum}{\@empty}}{}{(\@issuenum)}% Determine whether to display the issue number
    :\@firstpage--\pageref*{LastPage}. %
    \changeurlcolor{black}%
    \href{https://doi.org/\@doinum}{https://doi.org/\@doinum}%
}


%% DOI number
%% Create command to add a leading zero if 1 digit
\newcommand\twodigits[1]{%
	\ifnum#1<10%
		0\number#1
   	\else
		\number#1
	\fi
}

% Create command to add a leading zero if less than 4 digits
\newcommand\fourdigits[1]{%
\ifnum#1<10 
	000\number#1 
\else
	\ifnum#1<100 %
		00\number#1
	\else
           	\ifnum#1<1000 %
			0\number#1
		\else
			\ifnum#1<10000 %
				\number#1
			\else                   
					error
			\fi
		\fi
	\fi
\fi
}

% Create command to add a leading zero if less than 6 digits
\newcommand\sixdigits[1]{%
\ifnum#1<10 %
  00000\number#1 
\else
  \ifnum#1<100 %
    0000\number#1
  \else
    \ifnum#1<1000 %
      000\number#1
    \else
      \ifnum#1<10000 %
        00\number#1
      \else
        \ifnum#1<100000 %
          0\number#1
        \else
          \number#1
        \fi
      \fi
    \fi
  \fi
\fi
}

\doinum{10.32604/\@doiabbr.\fourdigits\@pubyear.\sixdigits\@articlenumber}%plan A
%\doinum{10.32604/\@articlenumber}%plan B

% For \@pubvolume, \@issuenum, and \@articlenumber: create command to cut leading zeros
\newcommand\cutdigits[1]{%
	\ifnum#1>0 %
		\number#1 
	\else
		\ifnum#1<10000 %
			\number#1
		\else             
			error
		\fi
	\fi
}

\newcommand{\pubvolume}[1]{\gdef\@pubvolume{\cutdigits{#1}}}%
\newcommand{\pubyear}[1]{\gdef\@pubyear{#1}}%
\newcommand{\copyrightyear}[1]{\gdef\@copyrightyear{#1}}%
\newcommand{\address}[2][]{\renewcommand{\firstargument}{#1}\gdef\@address{#2}}%
\newcommand{\corresfirstargument}{}%
\def\@corres{}%
\newcommand{\corres}[2][]{\renewcommand{\corresfirstargument}{#1}\gdef\@corres{#2}}%
\def\@conference{}%
\newcommand{\conference}[1]{\gdef\@conference{#1}}%
\def\@abstract{}%
\renewcommand{\abstract}[1]{\gdef\@abstract{#1}}%
\def\@externaleditor{}%
\newcommand{\externaleditor}[1]{\gdef\@externaleditor{#1}}%
\def\@datereceived{}%
\newcommand{\datereceived}[1]{\gdef\@datereceived{#1}}%
\def\@daterevised{}%
\newcommand{\daterevised}[1]{\gdef\@daterevised{#1}}%
\def\@dateaccepted{}%
\newcommand{\dateaccepted}[1]{\gdef\@dateaccepted{#1}}%
\def\@dateonlinefirst{}%
\newcommand{\dateonlinefirst}[1]{\gdef\@dateonlinefirst{#1}}%
\newcommand{\datepublished}[1]{\gdef\@datepublished{#1}}%
\def\@datecorrected{}%
\newcommand{\datecorrected}[1]{\gdef\@datecorrected{#1}}%
\def\@dateretracted{}%
\newcommand{\dateretracted}[1]{\gdef\@dateretracted{#1}}%
\newcommand{\history}[1]{\gdef\@history{#1}} %abort
\def\@pacs{}%
\newcommand{\PACS}[1]{\gdef\@pacs{#1}}%
\def\@msc{}%
\newcommand{\MSC}[1]{\gdef\@msc{#1}}%
\def\@jel{}%
\newcommand{\JEL}[1]{\gdef\@jel{#1}}%
\def\@keyword{}%
\newcommand{\keyword}[1]{\gdef\@keyword{#1}}%
\def\@issuenum{}%
\newcommand{\issuenum}[1]{\gdef\@issuenum{\cutdigits{#1}}}%
\def\@firstnote{}%
\newcommand{\firstnote}[1]{\gdef\@firstnote{#1}}%
\def\@secondnote{}%
\newcommand{\secondnote}[1]{\gdef\@secondnote{#1}}%
\def\@thirdnote{}%
\newcommand{\thirdnote}[1]{\gdef\@thirdnote{#1}}%
\def\@fourthnote{}%
\newcommand{\fourthnote}[1]{\gdef\@fourthnote{#1}}%
\def\@fifthnote{}%
\newcommand{\fifthnote}[1]{\gdef\@fifthnote{#1}}%
\def\@sixthnote{}%
\newcommand{\sixthnote}[1]{\gdef\@sixthnote{#1}}%
\def\@seventhnote{}%
\newcommand{\seventhnote}[1]{\gdef\@seventhnote{#1}}%
\def\@myeighthnote{}%
\newcommand{\myeighthnote}[1]{\gdef\@myeighthnote{#1}}%\@eighthnote will clah with \usepackage{mathcomp} For permille mark
\newcommand{\articlenumber}[1]{\gdef\@articlenumber{#1}}%
\def\@externalbibliography{}%
\newcommand{\externalbibliography}[1]{\gdef\@externalbibliography{#1}}%
\def\@reftitle{}%
\newcommand{\reftitle}[1]{\gdef\@reftitle{#1}}%
\def\@longauthorlist{}%
\newcommand{\longauthorlist}[1]{\gdef\@longauthorlist{#1}}%
\def\@addhighlights{}%
\newcommand{\addhighlights}[1]{\gdef\@addhighlights{#1}}%
\def\@CorrStatement{}%
\newcommand{\CorrStatement}[1]{\gdef\@CorrStatement{#1}}%
\newcommand{\textcorrstatement}{\textbf{Correction Statement:} This article has been republished with a minor change. The change does not affect the scientific content of the article and further details are available within the backmatter of the website version of this article.}
\def\@elocationid{}%
\newcommand{\elocationid}[1]{\gdef\@elocationid{\cutdigits{#1}}}% 2025.1.5 updated


%%%% Hyphenation
\RequirePackage[none]{hyphenat} % Prevent hyphenation throughout the document, meaning words will not be split even if they exceed the line width.
\sloppy % Loosens LaTeX's restrictions on line spacing and line length.

\regtotcounter{page} % to enable extracting the value of the counter "page" using the totcount package


%% ORCID 
%% Make Orcid icon
\newcommand{\orcidicon}{\includegraphics[width=0.32cm]{Definitions/logo-orcid.pdf}}

%% Define link and button for each author
\foreach \x in {A, ..., Z}{%
\expandafter\xdef\csname orcid\x\endcsname{\noexpand\href{https://orcid.org/\csname orcidauthor\x\endcsname}{\noexpand\orcidicon}}
}%


%%%% Journal name for the header
\newcommand{\journalname}{\@journalshort}

%%%%% Header and footer on first page
%%% The plain page style needs to be redefined because with \maketitle in the article class, LaTeX applies the the plain page style automatically to the first page.
\fancypagestyle{plain}{
    \fancyhf{} % clear default setting

    % ------------------ left ------------------
    \fancyhead[L]{\vspace{0pt}%
        \ifthenelse{\equal{\@journal}{rimni}}{%
            % rimni 
            \rule{0pt}{1.2cm}%
        }{%
            % other Journals
            \ifthenelse{\equal{\@status}{submit}}{%
                \rule{0pt}{1.2cm}%
            }{%
                \href{https://www.techscience.com/journal/\@journal}{%
                    {\includegraphics[height=1.2cm]{Definitions/\@journal-logo.pdf}}%
                }%
            }%
        }%
    }%

    % ------------------ right ------------------
    \fancyhead[R]{\vspace{0.3cm}%
        \ifthenelse{\equal{\@journal}{rimni}}{%
            % rimni 
            %\rule{0pt}{0.6cm}%
        }{%
            %  other Journals
            {\href{http://www.techscience.com}{%
                {\includegraphics[height=0.6cm]{Definitions/logo-tsp.pdf}}%
            }}%
        }%
    }%
    \rule{\textwidth}{0.4pt}%

    % ------------------ footer ------------------
    \fancyfoot[C]{%%%% Copyright information Plan A %\newcommand{\cright}
        \fontsize{8}{9}\selectfont 
        \ifthenelse{\equal{\@journal}{rimni}}{%
            % rimni 
            \begin{minipage}{1\textwidth}\changeurlcolor{black}
                \vspace{-6pt}This is an article distributed under the terms of the Creative Commons BY-NC-SA license.
                \end{minipage}
        }{%
            % other Journals
            \ifthenelse{\equal{\@status}{submit}}{%
                \begin{minipage}{1\textwidth}
                    \vspace{-6pt}\copyright{} {\@ \the\year} by the \@authornum. % if needed
                    Submitted to {\journalname} for % possible open access publication
                    under a Creative Commons Attribution 4.0 International License, which
                    permitted unrestricted use, distribution, and reproduction in any medium, provided the original
                    work is properly cited.% 
                \end{minipage} 
            }{%
                %\begin{minipage}{0.160\textwidth}
                %    \hspace{-0mm}%
                %    \vspace{2mm}%
                %    \href{http://creativecommons.org/}{%
                %        \includegraphics[width=0.95\textwidth]{Definitions/logo-ccby.pdf}
                %    }
                %\end{minipage}%
                \begin{minipage}{1\textwidth}\changeurlcolor{black}
                \vspace{-6pt} Copyright \copyright \ {\@copyrightyear} The \@authornum. Published by Tech Science Press. This work is licensed under a \href{https://creativecommons.org/licenses/by/4.0/}{Creative Commons Attribution 4.0 International License}, which permits unrestricted use, distribution, and reproduction in any medium, provided the original work is properly cited.
                \end{minipage}
            }
        }%
    }

    % ------------------ distance ------------------
    \setlength{\footskip}{36pt}
}



%% Maketitle part 1: DOI, Logo, Arttype, Title, Author
\renewcommand{\@maketitle}{
\noindent
{{\raggedright%
    \raisebox{+0cm}{\fontsize{8}{8}\selectfont
    \changeurlcolor{black}%
    \ifthenelse{\equal{\@journal}{rimni}}{%
        % rimni
    }{%
        % others
        \href{http://doi.org/10.32604/\@journal.\@pubyear.\sixdigits\@articlenumber}{http://doi.org/\@doinum}%
    }}}%
    \hfill%
    {\raggedleft%
    \raisebox{-1.3cm}{%
    \ifthenelse{\equal{\@journal}{rimni}}{%
        % rimni 
        \rule{0pt}{0.9cm} %
    }{%
        % ohers
        \ifthenelse{\equal{\@status}{submit}}{%
            \rule{0pt}{0.6cm}%
        }{%
            \href{https://www.techscience.com/doi/10.32604/\@journal.\@pubyear.\sixdigits\@articlenumber}{%
                \raisebox{0.6cm}{\includegraphics[height=0.9cm]{Definitions/logo-updates.pdf}}%
            }%
        }%
    }}}%
}

        \par
	\begin{flushleft}
		{%1
                \vspace{-1cm}
    		\fontsize{9}{9}\selectfont
		{\boldmath\bfseries{\underline{\@arttype}}}%	
 	   	\par%
    		}%1
    		{%2
   	 	\vspace{18pt}
  	  	\fontsize{14}{16}\selectfont
   	 	\boldmath\bfseries{\@Title}%Set Article Title format	
   	 	\par
   	 	\vspace{18pt}
   	 	}%2
   		{%3
    		\fontsize{11}{11}\selectfont
    		\boldmath\bfseries{\@Author}
    		\par
    		\vspace{6pt}
    		}%3
	\end{flushleft}%
	}

%% Commands for hanging indent
\newcommand{\dist}{0.42em}%\enspace=0.5em
\newcommand{\hang}{\hangafter=1\hangindent=\dist\noindent}


%% Maketitle part 2
\newcommand{\maketitlen}{ 
{%
	\begin{flushleft}
	\begin{spacing}{1.35}%Affiliation
	\leftskip0cm%Affiliation
	\fontsize{9}{9}\selectfont
	{%
	\ifthenelse{\equal{\firstargument}{1}}{}{%
	\hang}\@address
	\par
	}%
	{%
    	\ifthenelse{\equal{\@corres}{\@empty}}{}{%
      	 \hang{\hspace{0.05em}*}\@corres
       	 \par
    	}%
	}%
	{%
	\hang\ifthenelse{\equal{\@firstnote}{\@empty}}{}{{\textsuperscript{\#}}\@firstnote}%
	\par
	}
	{%
	\hang\ifthenelse{\equal{\@secondnote}{\@empty}}{}{{\textsuperscript{\S}}\@secondnote}
	\par
	}%
        {%
	\hang\ifthenelse{\equal{\@thirdnote}{\@empty}}{}{{\textsuperscript{$\dagger$}}\@thirdnote}	
	\par
	}%
	{%
	\hang\ifthenelse{\equal{\@fourthnote}{\@empty}}{}{{\textsuperscript{$\ddagger$}}\@fourthnote}
	\par
	}%
	{%
	\hang\ifthenelse{\equal{\@fifthnote}{\@empty}}{}{{{$^\|$}}\@fifthnote}
	\par
	}%
	{%
	\hang\ifthenelse{\equal{\@sixthnote}{\@empty}}{}{{\textsuperscript{\P}}\@sixthnote}
	\par
	}%
	{%
	\hang\ifthenelse{\equal{\@seventhnote}{\@empty}}{}{{\textsuperscript{**}}\@seventhnote}
	\par
	}%
	{%
	\hang\ifthenelse{\equal{\@myeighthnote}{\@empty}}{}{{\textsuperscript{$\dagger\dagger$}}\@myeighthnote}
	\par
	}%
	\vspace{6pt}
	\ifthenelse{\equal{\@externaleditor}{\@empty}}{}{\@externaleditor}
	\par
	\ifthenelse{\equal{\@status}{submit}}{Version {\@ \today} submitted to \journalname
}{%
	\ifthenelse{\equal{\@datereceived}{\@empty}}{}{Received: \@datereceived\ifthenelse{\equal{\@dateaccepted}{\@empty}}{}{; } }%
	%\ifthenelse{\equal{\@daterevised}{\@empty}}{}{Revised: \@daterevised\ifthenelse{\equal{\@dateaccepted}{\@empty}}{}{; } }%
	\ifthenelse{\equal{\@dateaccepted}{\@empty}}{}{%
	Accepted: \@dateaccepted\ifthenelse{\equal{\@dateonlinefirst}{\@empty}}{\ifthenelse{\equal{\@datepublished}{\@empty}}{}{; }}{; }%	
	}
	\ifthenelse{\equal{\@dateonlinefirst}{\@empty}}{}{%
	Online first: \@dateonlinefirst\ifthenelse{\equal{\@datepublished}{\@empty}}{}{; }%
	}%
	\ifthenelse{\equal{\@datepublished}{\@empty}}{}{Published: \@datepublished}%	
	\ifthenelse{\equal{\@datecorrected}{\@empty}}{}{; Corrected: \@datecorrected}%
	\ifthenelse{\equal{\@dateretracted}{\@empty}}{}{; Retracted: \@dateretracted}%
	\ifthenelse{\equal{\@retractiondate}{\@empty}}{}{\par\vspace{6pt}This paper has been retracted. A retraction notice was published on \@retractiondate{} in {\@journalshort.} {\@retractionnoticeyear};{\@retractionnoticevolume}{(\@retractionnoticeissue)}:\@retractionnoticeidnumber. https://doi.org/\@retractionnoticedoi}}%
% \par
% \bigskip
%\raggedright\textbf{Cite this article:} \papercitation %% not applicable
	\par
	\vspace{-4pt}%
	\end{spacing}
	\end{flushleft}
}
}


%%%% Abstract, keywords, PACS, MSC, JEL
\newcommand{\abstractkeywords}{
\fontsize{10}{12}\selectfont
\vspace{-8pt}

\ifthenelse{\equal{\@abstract}{\@empty}}{}{
	\noindent\textbf{ABSTRACT:\space}\@abstract
	\vspace{12pt}
	\par
}

\ifthenelse{\equal{\@keyword}{\@empty}}{}{
	\noindent\textbf{KEYWORDS:\space}\@keyword
	\vspace{12pt}
	\par
}
\ifthenelse{\equal{\@pacs}{\@empty}}{}{
	\noindent\textbf{PACS:\space}\@pacs
	\vspace{12pt}
	\par
}
\ifthenelse{\equal{\@msc}{\@empty}}{}{
	\noindent\textbf{MSC:\space}\@msc
	\vspace{12pt}
	\par
}
\ifthenelse{\equal{\@jel}{\@empty}}{}{
	\noindent\textbf{JEL CLASSIFICATION:\space}\@jel
	\vspace{12pt}
	\par
}
\vspace{4pt}
\hrule
\vspace{12pt}
\normalsize
}


%% Print maketitle and abstractkeywords
\AfterEndPreamble{
  \maketitle
  \let\maketitle\relax
  \maketitlen
  \let\maketitlen\relax
  \ifthenelse{\equal{\@status}{submit}}{\linenumbers}{}
  \abstractkeywords
}

\AtBeginDocument{
  \DeclareSymbolFont{AMSb}{U}{msb}{m}{n}% Declares the AMS blackboard bold font.
  \DeclareSymbolFontAlphabet{\mathbb}{AMSb} % Binds the \mathbb command to the AMSb blackboard bold font.
}


%% Font size in Tables and watermark in arttype retraction
\AtEndPreamble{
	\def\@tablesize{}
	\newcommand{\tablesize}[1]{\gdef\@tablesize{#1}}
	\let\oldtabularx\tabularx
	\renewcommand{\tabularx}{\ifthenelse{\equal{\@tablesize}{\@empty}}{\small}{\@tablesize}\oldtabularx}
}


%%%% Table of contents
\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}} % Dots between section title and page number
\renewcommand{\numberline}[1]{#1.~\space} % Increase space between number and title


%%%% Section headings
\setcounter{secnumdepth}{4} %i.e., section numbering depth, which defaults to 3 in the article class. To get paragraphs numbered and counted, increase the default value of secnumdepth to 4

\titleformat {\section} [block] {\raggedright \fontsize{11}{11}\selectfont\bfseries\boldmath} {\thesection\space} {0pt} {}
\titlespacing {\section} {0pt} {12pt} {6pt}

\titleformat {\subsection} [block] {\raggedright \fontsize{11}{11}\selectfont\itshape\bfseries\boldmath} {\thesubsection\space} {0pt} {}
\titlespacing {\subsection} {0pt} {12pt} {6pt}

\titleformat {\subsubsection} [block] {\raggedright \fontsize{11}{11}\selectfont\itshape} {\thesubsubsection\space} {0pt} {}
\titlespacing {\subsubsection} {0pt} {12pt} {6pt}

\titleformat {\paragraph} [block] {\raggedright \fontsize{11}{11}\selectfont} {} {0pt} {}
\titlespacing {\paragraph} {0pt} {12pt} {6pt}


%%%% Special section title style for back matter
\newcommand{\acknowledgement}[1]{
\vspace{12pt}\noindent{\fontsize{10}{11}\selectfont\textbf{Acknowledgement:} {#1}\par}}

\newcommand{\funding}[1]{
\vspace{12pt}\noindent{\fontsize{10}{11}\selectfont\textbf{Funding Statement:} {#1}\par}}

\newcommand{\authorcontributions}[1]{%
\vspace{12pt}\noindent{\fontsize{10}{11}\selectfont\textbf{Author Contributions:} {#1}\par}}

\newcommand{\availabilityofdataandmaterials}[1]{%
\vspace{12pt}\noindent{\fontsize{10}{11}\selectfont\textbf{Availability of Data and Materials:} {#1}\par}}

\newcommand{\ethicsapproval}[1]{%
\vspace{12pt}\noindent{\fontsize{10}{11}\selectfont\textbf{Ethics Approval:} {#1}\par}}

\newcommand{\informedconsent}[1]{%
\vspace{12pt}\noindent{\fontsize{10}{11}\selectfont\textbf{Informed Consent:} {#1}\par}}

\newcommand{\conflictsofinterest}[1]{%
\vspace{12pt}\noindent{\fontsize{10}{11}\selectfont\textbf{Conflicts of Interest:} {#1}\par}}

\newcommand{\useofartificialintelligence}[1]{
\vspace{12pt}\noindent{\fontsize{10}{11}\selectfont\textbf{Use of Artificial Intelligence:} {#1}\par}}

\newcommand{\supplementary}[1]{
\vspace{12pt}\noindent{\fontsize{10}{11}\selectfont\textbf{Supplementary Materials:} {#1}\par}}

\newcommand{\abbreviations}[2]{
\vspace{12pt}{\noindent\selectfont{\bfseries #1}}{%
\par\vspace{3pt}\noindent{\fontsize{10}{11}\selectfont #2}\par}}

% Use for special paragraph requirement in back matter
\newcommand{\backnotes}[2]{
\vspace{12pt}\noindent{\fontsize{10}{11}\selectfont\textbf{#1:} {#2}\par}}


%%%%% Define the appendix
\def\@appendixtitles{}
\newcommand{\appendixtitles}[1]{\gdef\@appendixtitles{#1}}

\def\@appendixsections{}
\newcommand{\appendixsections}[1]{\gdef\@appendixsections{#1}}

\def\@appendixstart{}
\newcommand{\appendixstart}[1]{\gdef\@appendixstart{#1}}

\renewcommand{\appendixstart}{%
\setcounter{section}{0}%
\setcounter{subsection}{0}%
\setcounter{subsubsection}{0}%
\setcounter{figure}{0}
\setcounter{table}{0}
\setcounter{scheme}{0}
\setcounter{chart}{0}
\setcounter{photo}{0}
\setcounter{boxenv}{0}
\setcounter{equation}{0}
\setcounter{theorem}{0}
\setcounter{lemma}{0}
\setcounter{corollary}{0}
\setcounter{proposition}{0} 
\setcounter{characterization}{0} 
\setcounter{property}{0} 
\setcounter{problem}{0} 
\setcounter{example}{0} 
\setcounter{examplesanddefinitions}{0} 
\setcounter{remark}{0} 
\setcounter{definition}{0} 
\setcounter{hypothesis}{0}
\setcounter{notation}{0}
\setcounter{algorithm}{0}
}

\renewcommand{\appendix}{%
%
\gdef\thesection{\@Alph\c@section}%
\gdef\thesubsection{\@Alph\c@section.\@arabic\c@subsection}%

\titleformat {\section} [block] {\raggedright\bfseries} {%
	\ifthenelse{\equal{\@appendixtitles}{yes}}{%in case of adding dot after serial numbers
		\appendixname~\thesection.%
		}{%
		\appendixname~\thesection~%
		}
	} {0pt} {}
\titlespacing {\section} {0pt} {12pt} {6pt}
%
\titleformat {\subsection} [block] {\raggedright\itshape\bfseries} {%
	\ifthenelse{\equal{\@appendixtitles}{yes}}{%
		\appendixname~\thesubsection.%
		}{%
		\appendixname~\thesubsection%
		}
	} {0pt} {}
\titlespacing {\section} {0pt} {12pt} {6pt}
%
\titleformat {\subsubsection} [block] {\raggedright\selectfont} {%
	\ifthenelse{\equal{\@appendixtitles}{yes}}{%
		\appendixname~\thesubsubsection.%
		}{%
		\appendixname~\thesubsubsection%
		}
	} {0pt} {}
\titlespacing {\section} {0pt} {12pt} {6pt}
%
\gdef\theHsection{\@Alph\c@section.}% for hyperref
\gdef\theHsubsection{\@Alph\c@section.\@arabic\c@subsection}% for hyperref
\csname appendixmore\endcsname
\renewcommand{\thefigure}{A\arabic{figure}}
\renewcommand{\thetable}{A\arabic{table}}
\renewcommand{\thescheme}{A\arabic{scheme}}
\renewcommand{\thechart}{A\arabic{chart}}
\renewcommand{\thephoto}{A\arabic{photo}}
\renewcommand{\theboxenv}{A\arabic{boxenv}}
\renewcommand{\theequation}{A\arabic{equation}}
\renewcommand{\thetheorem}{A\arabic{theorem}}
\renewcommand{\thelemma}{A\arabic{lemma}}
\renewcommand{\thecorollary}{A\arabic{corollary}}
\renewcommand{\theproposition}{A\arabic{proposition}} 
\renewcommand{\thecharacterization}{A\arabic{characterization}}
\renewcommand{\theproperty}{A\arabic{property}}
\renewcommand{\theproblem}{A\arabic{problem}}
\renewcommand{\theexample}{A\arabic{example}}
\renewcommand{\theexamplesanddefinitions}{A\arabic{examplesanddefinitions}}
\renewcommand{\theremark}{A\arabic{remark}}
\renewcommand{\thedefinition}{A\arabic{definition}}
\renewcommand{\thehypothesis}{A\arabic{hypothesis}}
\renewcommand{\thenotation}{A\arabic{notation}}
\renewcommand{\thealgorithm}{A\arabic{algorithm}}
}

%%%% Layout
\RequirePackage[left=2.54cm,
                right=2.54cm,
                top=2.54cm,
                bottom=2.54cm
                ]{geometry}

\linespread{1.08} 
\setlength{\parindent}{0.75cm}


%%%% Commands for landscape page with letter size
\newcommand{\startlandscape}{
	\clearpage
	\paperwidth=\pdfpageheight
	\paperheight=\pdfpagewidth
	\pdfpageheight=\paperheight
	\pdfpagewidth=\paperwidth
	% Adjust layout for letter paper (8.5 x 11 inches) with margins
	\newgeometry{layoutwidth=279.4mm, layoutheight=215.9mm, left=2.54cm, right=2.54cm, top=2.54cm, bottom=2.54cm}
	\fancyheadoffset{0pt}
	\captionsetup{margin={0cm,0cm}} 
}

\newcommand{\finishlandscape}{
	\clearpage
	\paperwidth=\pdfpageheight
	\paperheight=\pdfpagewidth
	\pdfpageheight=\paperheight
	\pdfpagewidth=\paperwidth
	\restoregeometry
	\fancyheadoffset{0pt} % No offset for header
	\captionsetup{margin={0cm,0cm}} % Reset captions margin to default
}


%%%% Figures and tables
\RequirePackage{newfloat}
\DeclareFloatingEnvironment[]{listing}
\DeclareFloatingEnvironment[name=Box]{boxenv}
\DeclareFloatingEnvironment[]{chart}
\DeclareFloatingEnvironment[]{scheme}
\DeclareFloatingEnvironment[]{photo}

\RequirePackage{caption} 
\captionsetup[figure]{position=bottom, margin=0cm, labelfont={bf, small, stretch=1.17}, labelsep=colon, textfont={small, stretch=1.17}, aboveskip=6pt, belowskip=-6pt, justification=justified}

\captionsetup[scheme]{position=bottom, margin=0cm, labelfont={bf, small, stretch=1.17}, labelsep=colon, textfont={small, stretch=1.17}, aboveskip=6pt, belowskip=-6pt, justification=justified}

\captionsetup[chart]{position=bottom, margin=0cm, labelfont={bf, small, stretch=1.17}, labelsep=colon, textfont={small, stretch=1.17}, aboveskip=6pt, belowskip=-6pt, justification=justified}

\captionsetup[phtot]{position=bottom, margin=0cm, labelfont={bf, small, stretch=1.17}, labelsep=colon, textfont={small, stretch=1.17}, aboveskip=6pt, belowskip=-6pt, justification=justified}

\captionsetup[listing]{position=top, margin=0cm, labelfont={bf, small, stretch=1.17}, labelsep=colon, textfont={small, stretch=1.17},  aboveskip=6pt, justification=justified}

\captionsetup[table]{position=top, margin=0cm, labelfont={bf, small, stretch=1.17}, labelsep=colon, textfont={small, stretch=1.17}, aboveskip=6pt, justification=justified}

\captionsetup[boxenv]{position=top, margin=0cm, labelfont={bf, small, stretch=1.17}, labelsep=colon, textfont={small, stretch=1.17}, aboveskip=6pt,justification=justified}

%% For table footnotes
\newsavebox{\@justcentbox}
\newcommand{\justifyorcenter}[1]{
\sbox \@justcentbox{#1}
\ifdim \wd \@justcentbox >\hsize #1
\else \centerline{#1} \fi
}

%% For text alignment in tables
\renewcommand\tabularxcolumn[1]{m{#1}} % vertical centering
\newcolumntype{C}{>{\centering\arraybackslash}X} % centered text in C columns
\newcolumntype{L}{>{\raggedright\arraybackslash}X} % centered text in L columns
\newcolumntype{R}{>{\raggedleft\arraybackslash}X} % centered text in R columns

%%%% Bullet lists
\setitemize{topsep=3pt,parsep=0pt,itemsep=0pt,leftmargin=*,labelsep=5.5mm,align=parleft}
\setenumerate{topsep=3pt,parsep=0pt,itemsep=0pt,leftmargin=*,labelsep=5.1mm,align=parleft}
\setlist[description]{itemsep=0mm}

%%%% Quote environment
\renewenvironment{quote}{
	\list{}{
		\listparindent=0pt
		\leftmargin=0.75cm
		\rightmargin=0.75cm
		\topsep=3pt
		\parsep=3pt
	}%
	\item\relax
	}
	{\endlist}


%% Link to supplementary material
\newcommand{\linksupplementary}[1]{\url{https://www.techscience.com/doi/\@doinum/s1}}

%%%% Header and footer (all pages except the first)
\renewcommand\headrule{} %% set line (from fancyhdr) in header to nothing
\pagestyle{fancy}
\fancyhf{} % clear

% Ensure necessary packages are included
\usepackage{fancyhdr}
\usepackage{ifthen}

% Set header content
\fancyhead[L]{%
    \ifodd\value{page} % 
        \fontsize{8}{8}\selectfont%
        \ifthenelse{\equal{\@status}{submit}}{%
            Version {\today} submitted to {\journalname} % 
        }{%
            \ifthenelse{\equal{\@datepublished}{\@empty}}{%
                {\journalname.\ }{\@pubyear} %  onlinefirst
            }{%
                {\journalname.\ }{\@pubyear};\@pubvolume(\@issuenum):\@elocationid % published
            }%
        }%
    \else
        \fontsize{8}{8}\selectfont\thepage %
    \fi
}

\fancyhead[R]{%
    \ifodd\value{page} % 
        \fontsize{8}{8}\selectfont\thepage% 
    \else
        \fontsize{8}{8}\selectfont%
        \ifthenelse{\equal{\@status}{submit}}{%
            Version {\today} submitted to {\journalname} % 
        }{%
            \ifthenelse{\equal{\@datepublished}{\@empty}}{%
                {\journalname.\ }{\@pubyear} %  onlinefirst
            }{%
                {\journalname.\ }{\@pubyear};\@pubvolume(\@issuenum):\@elocationid % published
            }%
        }%
    \fi
}

% \rfoot{%
%	   \fontsize{8}{8}\selectfont%
%	  {\url{https://doi.org/\@doinum}}%
%     }

% Ensure that the page style is applied
\pagestyle{fancy}


%% Article type "RETRACTION"
\def\@retractiondate{}% Date that the retraction notice was published
\newcommand{\retractiondate}[1]{\gdef\@retractiondate{#1}}
\def\@retractionnoticeyear{}% Year in which the retraction notice was published
\newcommand{\retractionnoticeyear}[1]{\gdef\@retractionnoticeyear{#1}}
\def\@retractionnoticevolume{} % Volume in which the retraction notice was published
\newcommand{\retractionnoticevolume}[1]{\gdef\@retractionnoticevolume{#1}}
\def\@retractionnoticeissue{} % Issue in which the retraction notice was published
\newcommand{\retractionnoticeissue}[1]{\gdef\@retractionnoticeissue{#1}}
\def\@retractionnoticeidnumber{}% Article Number in which the retraction notice was published
\newcommand{\retractionnoticeidnumber}[1]{\gdef\@retractionnoticeidnumber{#1}}
\def\@retractionnoticedoi{}  % DOI published retraction notice
\newcommand{\retractionnoticedoi}[1]{\gdef\@retractionnoticedoi{#1}}
\newcommand{\printretraction}{
\ifthenelse{\equal{\@retractiondate}{\@empty}}{}{%
	\RequirePackage{draftwatermark}
	\SetWatermarkText{RETRACTED}
	\SetWatermarkScale{0.65}
   }
}


%%%% Bibliography
\renewcommand\bibname{References} % Backwards compatibility for book production
\renewcommand\@biblabel[1]{#1.\hfill}
\def\thebibliography#1{
\emergencystretch 2em
%\linespread{1.1}% Line spacing factor, increases space between lines (1.44 times the normal line height)
\titleformat {\section} [block] {\raggedright \fontsize{10}{10}\selectfont\bfseries} {} {0pt} {}
%\ifthenelse{\equal{\@arttype}{}}{}{% to remove the sectin from the TOC in books
	\section{\@reftitle}
%}
\fontsize{10}{11}\selectfont
\list{{\arabic{enumi}}}{\def\makelabel##1{\hss{##1}}
\topsep=0\p@         % Top space for the list
\parsep=2\p@         % Paragraph space
\partopsep=0\p@      % Extra top space
\itemsep=0\p@        % Space between items
\labelsep=0.8mm      % Distance between number and content
\itemindent=0pt      % No indentation for items
\settowidth\labelwidth{\footnotesize[#1]}%
\leftmargin\labelwidth
\advance\leftmargin\labelsep
\usecounter{enumi}}
%\def\newblock{\ }
%\sloppy\clubpenalty4000\widowpenalty400
\sfcode`\.=1000\relax
}
\let\endthebibliography=\endlist

%%%% Publisher's note
\newcommand{\PublishersNote}{
\null\par\noindent\fontsize{9}{11}\selectfont\textbf{Disclaimer/Publisher's Note:}.}


%%% Copyright information Plan B At the End
%%%\AtEndDocument{\par \cright}
%\newcommand{\cright}
%{%
%	\vspace{12pt}
%	\noindent
%	\linespread{1} 
%	\fontsize{8.2}{8}\selectfont 
%	\ifthenelse{\equal{\@status}{submit}}{%
%		\begin{minipage}{1\textwidth}
%			\copyright{} {\@ \the\year} by the \@authornum. % if needed
%			Submitted to {\em \journalname} for % possible open access publication
%			under a Creative Commons Attribution 4.0 International License, which
%			permitted unrestricted use, distribution, and reproduction in any medium, provided the original
%			work is properly cited. % 
%		\end{minipage} %
%	}{%
%		\begin{minipage}{0.150\textwidth}
%			\hspace{-0mm}%
%			\vspace{2mm}%
%			\href{http://creativecommons.org/}{%
%				\includegraphics[width=0.95\textwidth]{Definitions/logo-ccby.pdf}
%			}
%		\end{minipage}%
%		\begin{minipage}{0.85\textwidth}
%			\vspace{-3pt}Copyright \copyright \ {\@copyrightyear} The \@authornum. Published by Tech Science Press.\\
%			This work is licensed under a Creative Commons Attribution 4.0 International License, 
%			which permits unrestricted use, distribution, and reproduction in any medium, 
%			provided the original work is properly cited.
%		\end{minipage}
%	}
%}


%\AtEndDocument{%
%  \par
%  \bigskip
%  \raggedright\textbf{Cite this article:} \papercitation
%}



%%%% For tables XML2PDF
\RequirePackage{seqsplit} % Use for split table column
  \newlength{\cellWidtha}
  \newlength{\cellWidthb}
  \newlength{\cellWidthc}
  \newlength{\cellWidthd}
  \newlength{\cellWidthe}
  \newlength{\cellWidthf}
  \newlength{\cellWidthg}
  \newlength{\cellWidthh}
  \newlength{\cellWidthi}
  \newlength{\cellWidthj}
  \newlength{\cellWidthk}
  \newlength{\cellWidthl}
  \newlength{\cellWidthm}
  \newlength{\cellWidthn}
  \newlength{\cellWidtho}
  \newlength{\cellWidthp}
  \newlength{\cellWidthq}
  \newlength{\cellWidthr}
  \newlength{\cellWidths}
  \newlength{\cellWidtht}
  \newlength{\cellWidthu}
  \newlength{\cellWidthv}
  \newlength{\cellWidthw}
  \newlength{\cellWidthx}
  \newlength{\cellWidthy}
  \newlength{\cellWidthz}
  \newlength{\cellWidthA}
  \newlength{\cellWidthB}
  \newlength{\cellWidthC}
  \newlength{\cellWidthD}
  \newlength{\cellWidthE}
  \newlength{\cellWidthF}
  \newlength{\cellWidthG}
  \newlength{\cellWidthH}
  \newlength{\cellWidthI}
  \newlength{\cellWidthJ}
  \newlength{\cellWidthK}
  \newlength{\cellWidthL}
  \newlength{\cellWidthM}
  \newlength{\cellWidthN}
  \newlength{\cellWidthO}
  \newlength{\cellWidthP}
  \newlength{\cellWidthQ}
  \newlength{\cellWidthR}
  \newlength{\cellWidthS}
  \newlength{\cellWidthT}
  \newlength{\cellWidthU}
  \newlength{\cellWidthV}
  \newlength{\cellWidthW}
  \newlength{\cellWidthX}
  \newlength{\cellWidthY}
  \newlength{\cellWidthZ}
 \newcommand{\PreserveBackslash}[1]{\let\temp=\\#1\let\\=\temp} % For table column setting in XML2PDF


%%%% Header and footer (all pages except the first) If continuous pagination is not used in the future.
%\renewcommand\headrule{} %% set line (from fancyhdr) in header to nothing
%\pagestyle{fancy}
%\lhead{{\fontsize{8}{8}\selectfont%
%		\ifthenelse{\equal{\@status}{submit}}{%
%			Version {\@ \today} submitted to {\journalname}% 
%		}{%
%			\ifthenelse{\equal{\@issuenum}{\@empty}}{%
%				{\journalname\ }{\@pubyear};\@pubvolume % No issue number
%			}{%
%				{\journalname\ }{\@pubyear};\@pubvolume(\@issuenum) % With issue number
%			}%
%		}\\%
%		\rule{\textwidth}{0.4pt}%
%	}% 
%}
%
%\rhead{
%{\fontsize{8}{8}\selectfont
%	\ifthenelse{\equal{\@continuouspages}{\@empty}}{%
%		\thepage{} of \pageref*{LastPage}% 
%	}{%
%		\thepage%
%	}%	
%}\\%
%\rule{\textwidth}{0.4pt}%
%}

\endinput