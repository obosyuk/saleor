import graphene
import pytest

from .....giftcard import GiftCardEvents
from .....giftcard.error_codes import GiftCardErrorCode
from ....tests.utils import get_graphql_content

GIFT_CARD_ADD_NOTE_MUTATION = """
    mutation addNote($id: ID!, $message: String!) {
        giftCardAddNote(id: $id, input: {message: $message}) {
            errors {
                field
                message
                code
            }
            giftCard {
                id
            }
            event {
                user {
                    email
                }
                message
            }
        }
    }
"""


def test_gift_card_add_note_as_staff_user(
    staff_api_client, permission_manage_gift_card, gift_card, staff_user
):
    assert not gift_card.events.all()
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.id)
    message = "nuclear note"
    variables = {"id": gift_card_id, "message": message}
    response = staff_api_client.post_graphql(
        GIFT_CARD_ADD_NOTE_MUTATION,
        variables,
        permissions=[permission_manage_gift_card],
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCardAddNote"]

    assert data["giftCard"]["id"] == gift_card_id
    assert data["event"]["user"]["email"] == staff_user.email
    assert data["event"]["message"] == message

    event = gift_card.events.get()
    assert event.type == GiftCardEvents.NOTE_ADDED
    assert event.user == staff_user
    assert event.parameters == {"message": message}


@pytest.mark.parametrize(
    "message",
    (
        "",
        "   ",
    ),
)
def test_gift_card_add_note_fail_on_empty_message(
    message, staff_api_client, permission_manage_gift_card, gift_card
):
    gift_card_id = graphene.Node.to_global_id("GiftCard", gift_card.id)
    variables = {"id": gift_card_id, "message": message}
    response = staff_api_client.post_graphql(
        GIFT_CARD_ADD_NOTE_MUTATION,
        variables,
        permissions=[permission_manage_gift_card],
    )
    content = get_graphql_content(response)
    data = content["data"]["giftCardAddNote"]
    assert data["errors"][0]["field"] == "message"
    assert data["errors"][0]["code"] == GiftCardErrorCode.REQUIRED.name
