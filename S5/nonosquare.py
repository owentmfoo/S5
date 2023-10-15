"""This is the no no square, no no don't read on there.
READ ON AT YOUR OWN RISK..."""

import random
from random import choice


def why():
    """The answer to life, the universe and everything, and much much more than that."""
    THEANSWER = _Why()
    THEANSWER.disp()
    return

class _Why:
    """internal class to generate the answer to life, the universe and everything, and much much more than that."""

    # the authors of S5
    Authors = ['Owen']

    # for people who "made the cut"
    Names = ['Owen the Kiwi', 'David', 'James', 'Cynthia', 'Isaac', 'Liam',
             'Ellie', 'Joe', 'Tom', 'Morgan', 'Jack', 'Adam',
             'Alex', 'Emily', 'Frances', 'Andrew', 'Hugh', 'Rob', 'Rachel', 'Burce the Corcodile',
             'Luke', 'Anith', 'Brain', 'Flanders', 'Nick', 'Ella', 'Ved', 'Ioan', 'Dylan', 'Connor', 'Ben', 'Tommy',
             'Zeynep', 'Matt', 'Tom', 'Saahil', 'Euan', 'Caitlin', 'Nicola',
             'Ollie', ' Nic'
             'Morgan the Mollusc', 'Cephy the cephalopod', ]

    def disp(self):
        output = self.random_string()
        print(output.capitalize())

    def random_string(self):
        n = random.randint(0, 100)
        if n < 10:
            output = self.quotes()
        elif n < 20:
            output = self.special_case()
        elif n < 50:
            output = self.phrase()
        else:
            output = self.sentence()
        return output

    def special_case(self):
        sc_list = [f"Because {choice(self.Authors)} said so.",
                   'how should I know?',
                   'the computer did it.',
                   'don''t ask!',
                   'the customer is always right.',
                   ]
        switch = random.randint(0, 100)
        if switch == 5:
            return f'in the beginning, God created the heavens and the earth, and {", and ".join(self.Authors)} created S5'
        elif switch == 42:
            return '42'
        else:
            return random.choice(sc_list)

    def phrase(self):
        ph_list = [
            # f"The answer is {self.noun()}",
            f'for the {self.nounded_verb()} {self.prepositional_phrase()}',
            f'to {self.present_verb()} {self.obj()}.',
            f'because {self.sentence()}'
        ]
        return choice(ph_list)

    def present_verb(self):
        pres_v_lst = [
            'fool',
            'please',
            'satisfy',
            'butter up'
        ]
        return choice(pres_v_lst)

    def preposition(self):
        prepo_lst = [
            'of',
            'from'
        ]
        return choice(prepo_lst)

    def prepositional_phrase(self):
        prepo_ph_lst = [
            f"{self.preposition()} {self.article()} {self.noun_phrase()}",
            f"{self.preposition()} {self.noun()}",
            f"{self.preposition()} {self.accusative_pronoun()}"
        ]
        return choice(prepo_ph_lst)

    def nounded_verb(self):
        nv_lst = ['love', 'approval', 'suggest', 'question']
        return choice(nv_lst)

    def proper_noun(self):
        return choice(self.Names + self.Authors)

    def subject(self):
        sbj_lst = [
            self.proper_noun(),
            self.nominative_pronoun(),
        ]
        return choice(sbj_lst)

    def nominative_pronoun(self):
        nompro_list = ['I', 'you', 'he', 'she', 'they']
        return choice(nompro_list)

    def sentence(self):
        return f'{self.subject()} {self.predicate()}.'

    def predicate(self):
        predic_lst = [
            f"{self.transitive_verb()} {self.obj()}",
            f"{self.intransitive_verb()}"
        ]
        return choice(predic_lst)

    def transitive_verb(self):
        trans_v_lst = [
            'threatened',
            'told',
            'asked',
            'helped',
            'obeyed'
        ]
        return choice(trans_v_lst)

    def intransitive_verb(self):
        intran_v_lst = [
            'insisted on it',
            'suggested it',
            'told me to',
            'wanted it',
            'knew it was a good idea',
            'wanted it that way'
        ]
        return choice(intran_v_lst)

    def obj(self):
        obj_lst = [
            self.accusative_pronoun(),
            f"{self.article()} {self.noun_phrase()}",
        ]
        return choice(obj_lst)

    def article(self):
        art_lst = [
            'the', 'some', 'a'
        ]
        return choice(art_lst)

    def noun_phrase(self):
        noun_ph_lst = [
            f"{self.noun()}", f"{self.noun()}", f"{self.noun()}", f"{self.noun()}", f"{self.noun()}", f"{self.noun()}",
            f"{self.adjective_phrase()} {self.noun()}", f"{self.adjective_phrase()} {self.noun()}"
        ]
        if random.randint(0, 4) == 3:
            return f"{self.adjective_phrase()} {self.noun_phrase()}"
        return choice(noun_ph_lst)

    def noun(self):
        noun_lst = [
            "engineer",
            "chief engineer",
            "fresher",
            "kid",
            "dad",
            "programmer",
            "badger's ringpiece",
            "rollhoop",
            "hammer",
            "DeWalt",
            "wind tunnel",
            "non technical member",
            "business team member",
            "object in the corner"
        ]
        return choice(noun_lst)

    def adjective_phrase(self):
        adj_ph_lst = [
            f"{self.adjective()}",
            f"{self.adjective()}",
            f"{self.adjective()}",
            f"{self.adverb()} {self.adjective()}",
        ]
        if random.randint(0, 6) == 1:
            return f"{self.adjective_phrase()} and {self.adjective_phrase()}"
        return choice(adj_ph_lst)

    def accusative_pronoun(self):
        accu_pron_lst = [
            'me',
            'all',
            'her',
            'him',
            'them'
        ]
        return choice(accu_pron_lst)

    def adverb(self):
        adv_lst = [
            'very',
            'not very',
            'not excessively',
            'just about',
            'nearly'
        ]
        return choice(adv_lst)

    def adjective(self):
        adj_list = [
            'tall',
            'bald',
            'young',
            'smart',
            'rich',
            'terrified',
            'good',
            "itsy bitsy tiny winey light grey",
            "bulletproof",
            "hard",
            "flexible"
        ]
        return choice(adj_list)

    def quotes(self):
        quotes = [
            "Life is worse now I have no chicken.",
            "There are new fresh coming in, you don’t need to bully me anymore!",
            "It’s a can. It should be in the CAN-opy.",
            "I don't know, I've never laid an egg.",
            "Why would Deacs think…?",
            "But I can see Joe being a special case.",
            "Why won’t you let me mate.",
            "I’m trying to do Maths.",
            "I do like a slap.",
            "150 is close to 100",
            "Pulleys are bulletproof.",
            "This is no fun at all!",
            "It's a bit like F1.",
            "Pigs aren’t square!"
        ]
        return choice(quotes)


if __name__ == '__main__':  # pragma: no cover
    for i in range(100):
        why()
