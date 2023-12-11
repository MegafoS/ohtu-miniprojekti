""" app.py - The main application """

from logic.citation_manager import CitationManager
from citations.citation_strings import ATTR_TRANSLATIONS
from tui.tui import Tui, Commands
from tui.tui_io import TuiIO
from app_msg import MSG


class App:
    """ THE APPLICATION !!! """

    def __init__(self, io=TuiIO()):
        self._tui = Tui(io)
        self._cm = CitationManager()

    def run(self):
        """ This starts the application """
        commands = {
            Commands.ADD:		self.__add,
            Commands.LIST:		self.__list,
            Commands.HELP:		self._tui.help,
            Commands.TAG:		self.__tag,
            Commands.BIB:		self.__bib,
            Commands.SEARCH:	self.__search,
            Commands.DELETE:	self.__delete,
            Commands.DROP:		self.__drop
        }

        self._tui.greet()

        while True:
            command = self._tui.menu()
            if command in (Commands.QUIT, "\0"):
                break
            if command in commands:
                commands[command]()
            else:
                self._tui.print_error( MSG.not_implemented )
                break

    def __bib(self):
        """Asks for .bib filename and creates new file
            of saved citations.
        """
        filename = self._tui.ask( MSG.Bib.ask_filename )
        if self._cm.create_bib_file(filename):
            self._tui.print_info(MSG.Bib.create_ok)
        else:
            self._tui.print_error(MSG.Bib.create_fail)

    def __search(self):
        """Method for searching all the citations with 
            certain tag.

        Returns:
            bool: False if there isn't any tags or citations.
                    True otherwise.
        """
        if self._cm.return_all_citations() == {}:
            self._tui.print_error( MSG.Search.fail_empty )
            return False

        if self._cm.get_all_tags() != {}:
            self._tui.print( MSG.Search.info_taglist )
            self._tui.print("\n".join(self._cm.get_all_tags()))
            tag = self._tui.ask( MSG.Search.ask_tag )
            plist = self._cm.get_plist_by_tag(tag)
            self.__print_plist(plist)
            return True

        self._tui.print_error(MSG.Search.fail_no_tags)
        return False

    def __list(self):
        """Prints out list of all citations.
        """
        plist = self._cm.get_plist()
        self.__print_plist(plist)


    def __print_plist(self, plist):
        if len(plist) == 0:
            self._tui.print( MSG.List.empty )
        for (c_id, label), attrs in plist:
            self._tui.print_item_entry(c_id, label)
            for key, value in attrs:
                self._tui.print_item_attribute( key, value )



    def __tag(self):
        """Adds tag for citation.

        Returns:
            bool: False if any error occurs. Otherwise True.
        """

        def validate_int(x):
            """Validator for citation id to be int.

            Args:
                x: user input for citation id

            Returns:
                bool: True if id is integer, otherwise False.
            """
            try:
                int(x)
            except ValueError:
                return False
            return True

        if self._cm.return_all_citations() == {}:
            self._tui.print_error( MSG.Tag.fail_empty )
            return False

        self._tui.print( MSG.Tag.info_list )
        self.__list()

        citation_id = self._tui.ask( MSG.Tag.ask_for_id, validate_int )

        if not self._cm.citation_exists(citation_id):
            self._tui.print_error( MSG.Tag.fail_unknown )
            return False

        citations_tag = self._cm.tag_by_citation(citation_id)

        if citations_tag != [] and not self._tui.yesno(MSG.Tag.info_retag):
            return False

        tag = self.__ask_tag()

        self._cm.add_tag_for_citation(citation_id, tag.lower())

        self._tui.print_info( MSG.Tag.success )
        return True

    def __ask_tag(self):
        """Checks if there is existing tags and asks user input for tag name.

        Returns:
            function: asking for new tag if there isn't existing tags or
                       also listing existing tags.
        """
        if self._cm.get_all_tags() != {}:
            self._tui.print( MSG.Tag.info_taglist )
            self._tui.print("\n".join(self._cm.get_all_tags()))
            return self._tui.ask( MSG.Tag.ask_tag )
        return self._tui.ask( MSG.Tag.ask_new_tag )


    def __add(self):
        """Asks the nessessary information and creates new citation.

        Returns:
            bool: False if user input isn't correct type,
                    True otherwise.
        """

        def validate_type(x):
            """Validator for citation type.

            Args:
                x: user input for citation type.

            Returns:
               bool: True if type is integer between 0 and 4,
                        False otherwise.
            """
            try:
                return int(x) > 0 and int(x) < 4
            except ValueError:
                pass
            return False

        def validate_year(x):
            """Validator for citation year.

            Args:
                x: user input for citation year.

            Returns:
                bool: True if year is integer between 0 and 2030,
                        False otherwise.
            """
            try:
                return int(x) > 0 and int(x) < 2030
            except ValueError:
                pass
            return False

        # citation label
        while True:
            label = self._tui.ask( MSG.Add.ask_label )
            if label == "\0":
                return False
            if self._cm.is_label_in_use(label):
                self._tui.print_error( MSG.Add.info_label_in_use )
                continue
            break

        # citation type
        try:
            ctype = int(self._tui.ask( MSG.Add.ask_type, validate_type ) )
        except ValueError:
            return False

        # other attributes
        attrs = self._cm.get_attrs_by_ctype(ctype)
        adict={}
        for attr in attrs:
            adict[attr] = self._tui.ask(
                f"{ATTR_TRANSLATIONS[attr]} ({attr})",
                validate_year if attr == "year" else lambda x: True
            )

        # add the tag
        tag = self.__ask_tag() \
            if self._tui.yesno( MSG.Add.ask_add_tag ) else ""

        if self._cm.add_citation(ctype, label, tag, adict):
            self._tui.print_info(MSG.Add.success)
        else:
            self._tui.print_error( MSG.Add.fail )


    def __drop(self):
        """Clears all the tables in database.
        """
        if self._tui.yesno( MSG.Drop.ask_sure ):
            self._cm.clear_all()
            self._tui.print_info( MSG.Drop.success )
        else:
            self._tui.print( MSG.Drop.aborted )

    def __delete(self):
        """Deletes one citation from database.
        """
        citation_id = self._tui.ask( MSG.Delete.ask_id )
        try:
            citation_id = int(citation_id)
        except ValueError:
            self._tui.print_error( MSG.Delete.fail )
            return
        if self._cm.delete_citation(citation_id):
            self._tui.print_info( MSG.Delete.success )
        else:
            self._tui.print_error( MSG.Delete.fail )


if __name__ == "__main__":
    app = App()
    app.run()
